import base64
import copy
import datetime
import textwrap
import html
import json
import re

import plotly.io as pio
from plotly.offline import get_plotlyjs, get_plotlyjs_version

# Same Plotly.js version as your installed plotly Python package, so figures render identically.
PLOTLY_CDN = f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js"

STYLE = dict(
    font="Montserrat, sans-serif",
    ink="#1f2733",
    sub="#4f5a68",
    rule="#e6e8ec",
    link="#1775c9",
)


def _slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "chart").lower()).strip("-")
    return (s[:40] or "chart")


def _thin_ticks(vals, max_n):
    """Keep first, last and evenly spaced ticks in between."""
    vals = list(vals)
    if len(vals) <= max_n:
        return vals
    step = (len(vals) - 1) / (max_n - 1)
    return [vals[round(i * step)] for i in range(max_n)]


def _axes(fig, letter):
    return [getattr(fig.layout, k) for k in fig.layout if re.fullmatch(letter + r"axis\d*", k)] \
        or [getattr(fig.layout, letter + "axis")]


def _logo_src(logo_path):
    """Return a data-URI (for local files) or the URL unchanged."""
    if logo_path.startswith("http"):
        return logo_path
    with open(logo_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def _add_margin_logo(logo_path, fig):
    """Place logo in the figure's bottom margin (below the plot area, above the figure edge)."""
    source = _logo_src(logo_path)
    current_b = fig.layout.margin.b
    fig.update_layout(margin_b=max(current_b if current_b is not None else 40, 95))
    existing = list(fig.layout.images) if fig.layout.images else []
    existing.append(dict(
        source=source,
        xref="paper", yref="paper",
        x=0.99, y=-0.08,
        sizex=0.15, sizey=0.09,
        xanchor="right", yanchor="top",
        layer="above",
    ))
    fig.layout.images = existing


def _is_category(fig, ax):
    if ax.type == "category":
        return True
    if ax.type not in (None, "-"):
        return False
    name = ax.plotly_name.replace("axis", "")  # xaxis2 -> x2
    for t in fig.data:
        ref = getattr(t, "xaxis", None) or "x"
        if ref == name or (ref == "x" and name == "x"):
            xs = getattr(t, "x", None)
            if xs is not None and len(xs) and isinstance(next(iter(xs)), str):
                return True
    return False


def _default_mobile(fig, margin_scale, text_scale, max_ticks, base_font):
    """Automatic phone-friendly changes, applied to a copy of the desktop figure."""
    m = fig.layout.margin
    fig.update_layout(margin=dict(
        l=max(10, round((m.l if m.l is not None else 80) * margin_scale)),
        r=max(10, round((m.r if m.r is not None else 80) * margin_scale)),
        t=max(10, round((m.t if m.t is not None else 40) * margin_scale)),
        b=max(10, round((m.b if m.b is not None else 60) * margin_scale)),
    ))
    for a in fig.layout.annotations:
        size = a.font.size or base_font
        a.font.size = round(size * text_scale, 1)
    for letter in ("x", "y"):
        for ax in _axes(fig, letter):
            ax.tickfont.size = round((ax.tickfont.size or base_font) * text_scale, 1)
            if ax.title.font.size or ax.title.text:
                ax.title.font.size = round((ax.title.font.size or base_font) * text_scale, 1)
            if letter == "x":
                if ax.tickvals is not None:
                    keep = _thin_ticks(ax.tickvals, max_ticks)
                    if ax.ticktext is not None:
                        txt = dict(zip(ax.tickvals, ax.ticktext))
                        ax.ticktext = [txt[v] for v in keep]
                    ax.tickvals = keep
                elif _is_category(fig, ax):
                    # Plotly silently drops crowded category labels; never lose a category
                    ax.dtick = 1
                else:
                    ax.nticks = max_ticks
    # a visible legend goes in one horizontal row above the plot
    named = [t for t in fig.data if getattr(t, "name", None) and t.showlegend is not False]
    if fig.layout.showlegend is not False and len(named) > 1:
        fig.update_layout(legend=dict(orientation="h", x=0, xanchor="left", y=1.02,
                                      yanchor="bottom", title_text="",
                                      font_size=round(base_font * text_scale, 1)))
    return fig


def _prepare(fig, height, allow_zoom, top_margin):
    """Copy the figure and make it web-ready: autosize, no Plotly title, fixed axes."""
    fig = copy.deepcopy(fig)
    title = fig.layout.title.text
    if top_margin is not None and (fig.layout.margin.t is None or fig.layout.margin.t > top_margin):
        # a big top margin usually held a Plotly title, which now lives in HTML
        fig.update_layout(margin_t=top_margin)
    fig.update_layout(title_text=None, width=None, autosize=True, height=height,
                      dragmode=False if not allow_zoom else fig.layout.dragmode)
    if not fig.layout.font.family:
        fig.update_layout(font_family=STYLE["font"])
    if not fig.layout.hoverlabel.font.family:
        fig.update_layout(hoverlabel_font_family=STYLE["font"])
    if not allow_zoom:
        # stops a phone user's scroll gesture turning into an accidental zoom
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
    return fig, title


def _plotlyjs_loader(include_plotlyjs):
    """Load Plotly.js once per page, however many charts there are."""
    if include_plotlyjs == "inline":
        return f"<script>{get_plotlyjs()}</script>\n"
    if include_plotlyjs == "cdn":
        return (
            "<script>window.swcPlotly = window.swcPlotly || new Promise(function (ok, fail) {\n"
            "  if (window.Plotly) return ok(window.Plotly);\n"
            "  var s = document.createElement('script');\n"
            f"  s.src = '{PLOTLY_CDN}'; s.onload = function () {{ ok(window.Plotly); }};\n"
            "  s.onerror = fail; document.head.appendChild(s);\n"
            "});</script>\n"
        )
    return ""  # False: the page already loads Plotly.js itself


# ----------------------------------------------------------------------------- main
def make_web_chart(fig, *, title=None, subtitle=None, caption=None, source=None, note=None,
                   logo_path=None, height=None, mobile_height=None, breakpoint=600, mobile=None,
                   auto_mobile=True, margin_scale=0.55, text_scale=0.85, max_ticks=4,
                   allow_zoom=False, top_margin=40, include_plotlyjs="cdn", chart_id=None,
                   style=None):
    """Return the embeddable HTML snippet for a Plotly figure.

    fig             A plotly.graph_objects.Figure. It is copied, never modified.
    title           Headline. Defaults to the figure's own title (removed from the chart).
    subtitle        One or two sentences saying what is measured, and in which units.
    source          Source line under the chart. May contain HTML links.
    note            Optional extra line under the subtitle, e.g. "Tap a line to see values."
    height          Desktop chart height in px (default: the figure's height, or 500).
    mobile_height   Chart height below the breakpoint (default: 85% of desktop height).
    breakpoint      Container width in px below which the mobile layout is used.
    mobile          Optional function(fig) that edits the mobile copy after the automatic
                    changes, e.g. shortening labels or hiding annotations.
    auto_mobile     Set False to skip the automatic mobile changes and use only `mobile`.
    allow_zoom      Default False: no drag-to-zoom (it hijacks scrolling on phones).
    top_margin      Cap on the chart's top margin in px (the title is HTML now, so the space
                    Plotly reserved for it is wasted). None keeps the figure's own margin.
    include_plotlyjs "cdn" (default), "inline" (self-contained, ~4.5 MB, works offline),
                    or False (your site already loads Plotly.js).
    style           Dict overriding colors/font in STYLE.
    """
    st = {**STYLE, **(style or {})}
    height = height or fig.layout.height or 500
    mobile_height = mobile_height or round(height * 0.85)

    desk, fig_title = _prepare(fig, height, allow_zoom, top_margin)
    title = title if title is not None else fig_title
    mob = copy.deepcopy(desk)
    mob.update_layout(height=mobile_height)
    base_font = desk.layout.font.size or 12
    if auto_mobile:
        _default_mobile(mob, margin_scale, text_scale, max_ticks, base_font)
    if mobile:
        mobile(mob)
    if logo_path:
        _add_margin_logo(logo_path, desk)

    cid = chart_id or "swc-" + _slug(title)
    desk_json = json.loads(pio.to_json(desk, validate=False, remove_uids=True))
    mob_json = json.loads(pio.to_json(mob, validate=False, remove_uids=True))
    mob_data = None if mob_json["data"] == desk_json["data"] else mob_json["data"]
    payload = json.dumps({
        "desk": desk_json, "mobLayout": mob_json["layout"], "mobData": mob_data,
        "bp": breakpoint,
        "config": {"responsive": True, "displayModeBar": False, "displaylogo": False,
                   "scrollZoom": False},
    }, separators=(",", ":"))

    def esc(t):  # titles are plain text; source/note may include deliberate HTML
        return html.escape(re.sub(r"<[^>]+>", " ", t)).strip() if t else ""

    parts = [f'<figure class="swc" id="{cid}-fig">']
    if title:
        parts.append(f'  <div class="swc-title" role="heading" aria-level="3">{esc(title)}</div>')
    if subtitle:
        parts.append(f'  <p class="swc-sub">{esc(subtitle)}</p>')
    if note:
        parts.append(f'  <p class="swc-note">{note}</p>')
    parts.append(f'  <div class="swc-plot" id="{cid}" role="img" '
                 f'aria-label="{html.escape(esc(title) or "Chart")}"></div>')
    if caption:
        parts.append(f'  <p class="swc-caption">{caption}</p>')
    if source:
        parts.append(f'  <figcaption class="swc-src">{source}</figcaption>')
    parts.append("</figure>")

    css = f"""<style>
.swc {{ font-family: {st['font']}; max-width: 900px; margin: 2rem auto; padding: 0;
        box-sizing: border-box; }}
.swc .swc-title {{ font-weight: 800; font-size: clamp(1.25rem, 3.2vw, 1.9rem); line-height: 1.15;
                  color: {st['ink']}; margin: 0 0 .5rem; }}
.swc .swc-sub, .swc .swc-note {{ color: {st['sub']}; font-size: 1rem; line-height: 1.4;
                               margin: 0 0 .5rem; }}
.swc .swc-note {{ font-size: .875rem; }}
.swc .swc-plot {{ width: 100%; margin-top: .5rem; }}
.swc .swc-caption {{ color: {st['sub']}; font-size: .875rem; line-height: 1.4;
                    margin: .5rem 0 .25rem; }}
.swc .swc-src {{ border-top: 2px solid {st['rule']}; padding-top: .6rem; margin-top: .25rem;
                color: {st['sub']}; font-size: .8rem; line-height: 1.4; }}
.swc .swc-src a {{ color: {st['link']}; }}
</style>"""

    js = f"""<script>
(function () {{
  var P = {payload};
  var el = document.getElementById('{cid}');
  var mode = null;
  function render() {{
    var narrow = el.clientWidth < P.bp;
    if (narrow === mode) return;
    mode = narrow;
    window.Plotly.react(el, narrow && P.mobData ? P.mobData : P.desk.data,
                        narrow ? P.mobLayout : P.desk.layout, P.config);
  }}
  function start() {{
    render();
    if (window.ResizeObserver) new ResizeObserver(render).observe(el);
    else window.addEventListener('resize', render);
  }}
  if (window.swcPlotly) window.swcPlotly.then(start); else start();
}})();
</script>"""

    return (f"<!-- Chart: {esc(title)} (generated by web_chart.py) -->\n"
            + css + "\n" + _plotlyjs_loader(include_plotlyjs) + "\n".join(parts) + "\n" + js + "\n")


def write_web_chart(fig, path, *, font_link=True, **kwargs):
    """Write a preview page, an embed snippet, and a PNG thumbnail.

    Writes three files:
      <path>            Full HTML preview page.
      <path>_embed.html Snippet to paste into the blog.
      <path>.png        PNG thumbnail (900 px wide, 2x scale).

    font_link   Include the Google Fonts link for Montserrat in the preview page.
                (Your site already loads it, so the embed snippet leaves it out.)
    Other keyword arguments go to make_web_chart().
    """
    snippet = make_web_chart(fig, **kwargs)

    embed_kwargs = {k: v for k, v in kwargs.items() if k not in ('caption', 'source')}
    embed_snippet = make_web_chart(fig, **embed_kwargs)
    embed_path = re.sub(r"\.html?$", "", path) + "_embed.html"
    with open(embed_path, "w", encoding="utf-8") as f:
        f.write(embed_snippet)

    font = ('<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800'
            '&display=swap" rel="stylesheet">\n') if font_link else ""
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chart preview</title>
{font}<style>body {{ margin: 0; padding: 16px; background: #fff; }}</style>
</head><body>
{snippet}</body></html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)

    height = kwargs.get('height') or fig.layout.height or 500
    top_margin = kwargs.get('top_margin', 40)
    allow_zoom = kwargs.get('allow_zoom', False)
    png_fig, png_title = _prepare(fig, height, allow_zoom, top_margin)
    title_text = kwargs.get('title') if kwargs.get('title') is not None else png_title
    subtitle_text = kwargs.get('subtitle')

    extra_t = (28 if title_text else 0) + (22 if subtitle_text else 0)
    if extra_t:
        cur_t = png_fig.layout.margin.t if png_fig.layout.margin.t is not None else top_margin
        new_t = cur_t + extra_t
        png_fig.update_layout(margin_t=new_t)
        if title_text:
            png_fig.add_annotation(
                text=title_text, xref='paper', yref='paper',
                x=0, y=1 + (new_t - 6) / height,
                showarrow=False,
                font=dict(size=15, color=STYLE['ink'], family=STYLE['font']),
                xanchor='left', yanchor='top',
            )
        if subtitle_text:
            png_fig.add_annotation(
                text=subtitle_text, xref='paper', yref='paper',
                x=0, y=1 + (new_t - 6 - 28) / height,
                showarrow=False,
                font=dict(size=11, color=STYLE['sub'], family=STYLE['font']),
                xanchor='left', yanchor='top',
            )

    logo_path = kwargs.get('logo_path')
    if logo_path:
        _add_margin_logo(logo_path, png_fig)
    png_fig.update_layout(width=900)
    png_path = re.sub(r"\.html?$", "", path) + ".png"
    png_fig.write_image(png_path, scale=2)

    return path, embed_path, png_path


def add_logo(logo_path, fig, x=0.99, y=1.15):
    """
    Add logo to the top-right corner of a figure (base64-encodes local files).

    :param str logo_path: Path to logo image, or a public URL (preferred for blog export)
    :param go.Figure fig: Plotly figure
    :param float x: Right edge of the logo in paper coordinates (default 0.99)
    :param float y: Top edge of the logo in paper coordinates (default 1.10)
    :return go.Figure fig: Figure with logo added
    """
    if logo_path.startswith("http"):
        source = logo_path
    else:
        with open(logo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        source = f"data:image/png;base64,{encoded_string}"

    sizex, sizey = 0.144, 0.108
    fig.layout.images = [dict(
        source=source,
        xref="paper",
        yref="paper",
        x=x,
        y=y,
        sizex=sizex,
        sizey=sizey,
        xanchor="right",
        yanchor="top",
    )]
    return fig


def add_copyright(logo_path, fig, x=0.99, y=1.01):
    """
    Add logo and copyright notice to the top-right corner of a figure.

    x and y are paper coordinates: 0–1 spans the plot area, and y > 1
    goes into the top margin. Increase the figure's top margin
    (e.g. margin=dict(t=80)) if the logo or text is clipped.

    :param str logo_path: Path or URL to logo image
    :param go.Figure fig: Plotly figure
    :param float x: Right edge of the logo in paper coordinates (default 0.99)
    :param float y: Top edge of the logo in paper coordinates (default 1.10)
    :return go.Figure fig: Figure with logo and copyright added
    """
    sizex, sizey = 0.12, 0.09
    fig.layout.images = [dict(
        source=logo_path,
        xref="paper",
        yref="paper",
        x=x,
        y=y,
        sizex=sizex,
        sizey=sizey,
        xanchor="right",
        yanchor="top",
    )]
    yr = datetime.date.today().year
    fig.add_annotation(
        text=f"© {yr} SolarWAVE Action. All Rights Reserved.",
        align='right',
        showarrow=False,
        xref='paper',
        yref='paper',
        x=x - sizex - 0.01,
        y=y - sizey / 2,
        xanchor='right',
        yanchor='middle',
        font=dict(color="gray", size=8),
        borderwidth=0,
    )
    return fig


def write_html_with_fonts(fig, write_path):
    html = fig.to_html(full_html=True,
                       include_plotlyjs='cdn',
                       config={"responsive": True, "displaylogo": False})
    font_link = (
              '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
              '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
              '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">\n')
    # Re-layout after fonts load — Plotly renders before async Google Fonts arrive,
    # so without this the fallback sans-serif is used permanently.
    font_ready_script = (
        '<script>\n'
        'document.fonts.ready.then(function() {\n'
        '  var gd = document.querySelector(".plotly-graph-div");\n'
        '  if (gd) Plotly.relayout(gd, {"font.family": "Montserrat, sans-serif"});\n'
        '});\n'
        '</script>\n')
    html = html.replace('</head>', font_link + '</head>', 1)
    html = html.replace('</body>', font_ready_script + '</body>', 1)
    with open(write_path, 'w') as f:
        f.write(html)


def write_fig(fig, path, title, caption=None, logo_path=None, logo_x=0.99):
    """
    Save a figure as both PNG (with visible title/caption) and HTML (title/caption in metadata only).

    :param go.Figure fig: Plotly figure without title or caption annotations
    :param str path: Output path without file extension
    :param str title: Chart title
    :param str caption: Optional caption text (HTML allowed for PNG; stripped for meta tag)
    :param str logo_path: Optional path or URL to logo image
    """
    # PNG — add title and caption as visible annotations on a copy
    fig_png = copy.deepcopy(fig)
    if logo_path is not None:
        fig_png = add_logo(logo_path, fig_png, x=logo_x)
    fig_png.add_annotation(
        text=title,
        xref='paper', yref='paper',
        x=0.01, y=1.1,
        showarrow=False,
        font=dict(size=14),
        xanchor='left', yanchor='top',
    )
    if caption is not None:
        fig_png.add_annotation(
            text=caption,
            xref='paper', yref='paper',
            x=0, y=-0.3,
            showarrow=False,
            font=dict(size=9),
            xanchor='left', yanchor='bottom',
            align='left',
        )
    fig_png.update_layout(
        margin=dict(l=40, r=40, t=60, b=140),
        width=800,
        font_family="Montserrat, sans-serif",
        title_font_family="Montserrat, sans-serif",
    )
    fig_png.write_image(path + '.png', scale=3)

    if logo_path is not None:
        fig = add_logo(logo_path, fig)
    # HTML — no visible title/caption; embed as <meta> tags instead
    html = fig.to_html(full_html=True,
                       include_plotlyjs='cdn',
                       config={"responsive": True, "displaylogo": False})
    plain_caption = re.sub(r'<[^>]+>', '', caption) if caption else ''
    meta_tags = (
        f'<meta name="title" content="{title}">\n'
        + (f'<meta name="description" content="{plain_caption}">\n' if caption else '')
    )
    font_link = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap" rel="stylesheet">\n'
    )
    font_ready_script = (
        '<script>\n'
        'document.fonts.ready.then(function() {\n'
        '  var gd = document.querySelector(".plotly-graph-div");\n'
        '  if (gd) Plotly.relayout(gd, {"font.family": "Montserrat, sans-serif"});\n'
        '});\n'
        '</script>\n'
    )
    html = html.replace('</head>', meta_tags + font_link + '</head>', 1)
    html = html.replace('</body>', font_ready_script + '</body>', 1)
    with open(path + '.html', 'w') as f:
        f.write(html)
