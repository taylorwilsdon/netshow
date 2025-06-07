"""Styles for the NetshowApp."""

CSS = """
$bg0: #103c48;
$bg1: #184956;
$bg2: #2d5b69;
$bg3: #1d3b45;
$fg0: #adbcbc;
$fg1: #cad8d9;
$accent: #4695f7;

Screen {
    background: $bg0;
    color: $fg0;
}

Header, Footer {
    background: $bg1;
    color: $fg1;
}

#status_bar {
    background: $bg2;
    color: $fg1;
    height: 3;
    padding: 0 1;
}

Vertical {
    width: 100%;
    height: 1fr;
}

DataTable {
    background: $bg0;
    color: $fg0;
    width: 100%;
    height: 1fr;
}

DataTable .header {
    background: $bg1;
    color: $fg1;
}

/* Detail screen styling */
#detail_title {
    background: $bg2;
    color: $fg1;
    height: 3;
    padding: 0 1;
    text-align: center;
    margin: 1 0;
}

#main_content {
    height: auto;
    margin: 0 1;
}

#connection_details, #process_info {
    background: $bg3;
    padding: 1;
    margin: 0 1 1 0;
    border: tall $bg2;
    height: auto;
    width: 1fr;
}

.section_header {
    background: $bg2;
    color: $fg1;
    padding: 0 1;
    text-align: center;
    margin: 0 0 1 0;
    height: 1;
}

.detail_item {
    margin: 0 0 1 0;
    padding: 0 1;
}

#back_button {
    margin: 1 0;
    background: $bg2;
    color: $fg1;
    border: tall $bg1;
    width: 30;
    height: 3;
}

#back_button:hover {
    background: $accent;
}

Button:focus {
    background: $accent;
}
"""
