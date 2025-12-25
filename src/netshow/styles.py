"""Styles for the NetshowApp - Solarized Dark Theme."""

CSS = """
/* === SOLARIZED DARK COLOR PALETTE === */
$base03: #002b36;
$base02: #073642;
$base01: #586e75;
$base00: #657b83;
$base0: #839496;
$base1: #93a1a1;
$base2: #eee8d5;
$base3: #fdf6e3;

$yellow: #b58900;
$orange: #cb4b16;
$red: #dc322f;
$magenta: #d33682;
$violet: #6c71c4;
$blue: #268bd2;
$cyan: #2aa198;
$green: #859900;


/* === METRICS ROW === */
#metrics_row {
    height: 3;
    margin: 0;
    padding: 0 1;
    width: 100%;
    align: center middle;
}

.metric {
    background: $base02;
    color: $base1;
    border: solid $base01;
    padding: 0 1;
    margin: 0;
    text-style: bold;
    content-align: center middle;
    width: auto;
    min-width: 8;
}

#conn_metric {
    border: solid $blue;
    color: $blue;
}

#active_metric {
    border: solid $green;
    color: $green;
}

#listen_metric {
    border: solid $cyan;
    color: $cyan;
}

#bandwidth_metric {
    border: solid $orange;
    color: $orange;
}

/* === BANDWIDTH SPARKLINE === */
#bandwidth_spark {
    width: 100%;
    height: 2;
    background: $base02;
    margin: 0;
    padding: 0 1;
}

Sparkline > .sparkline--max-color {
    color: $orange;
}

Sparkline > .sparkline--min-color {
    color: $cyan;
}

/* === FILTER CONTAINER === */
#filter_container {
    height: 3;
    margin: 0;
    padding: 0 1;
}

#filter_input {
    background: $base02;
    color: $base1;
    border: solid $magenta;
    height: 1;
    padding: 0 1;
}

#filter_input:focus {
    background: $base03;
    border: solid $cyan;
    color: $base1;
}


/* === GLOBAL STYLES === */
Screen {
    background: $base03;
    color: $base0;
}

/* === HEADER & FOOTER === */
Header {
    background: $base02;
    color: $base1;
    border-bottom: solid $base01;
    text-style: bold;
    height: 2;
}

Footer {
    background: $base02;
    color: $base1;
    height: 1;
}

/* === STATUS BAR === */
#stats_container {
    height: auto;
    margin: 0;
    border: solid $base01;
    padding: 0;
}

#status_bar {
    background: $base02;
    color: $base1;
    height: 1;
    padding: 0 1;
    border: none;
    margin: 0;
}

/* === LAYOUT CONTAINERS === */
Vertical, Container, Horizontal {
    border: none;
    padding: 0;
    margin: 0;
}

Vertical {
    width: 100%;
    height: 1fr;
}

/* === EDGE BORDER FIX === */
#connection_details {
    border-right: $base1;
}

#process_info {
    border-left: none;
}

/* === DATA TABLE STYLING === */
DataTable {
    background: $base03;
    color: $base0;
    width: 100%;
    height: 1fr;
    border: none;
    margin: 0;
}

#connections_table {
    border: none !important;
}

DataTable > .datatable--header {
    background: $base02;
    color: $base1;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: $base01;
    color: $base2;
    text-style: bold;
}

DataTable > .datatable--hover {
    background: $base02;
    color: $base1;
}

DataTable:focus > .datatable--cursor {
    background: $blue;
    color: $base3;
    text-style: bold;
}

/* === DETAIL SCREEN STYLING === */
#detail_title {
    background: $base02;
    color: $base1;
    height: 5;
    padding: 1 2;
    text-align: center;
    text-style: bold;
    margin: 0;
}

#main_content {
    height: auto;
    margin: 0;
    padding: 0;
    border: none;
    width: 100%;
}

#connection_details, #process_info {
    background: $base02;
    padding: 2;
    margin: 0;
    height: auto;
    width: 1fr;
}

.section_header {
    background: $base01;
    color: $base1;
    padding: 1 2;
    text-align: center;
    text-style: bold;
    margin: 0 0 1 0;
    height: 10;
}

.detail_title {
    margin: 0 0 1 0;
    padding: 1 1;
    color: $base1;
    text-style: bold;
    background: $base01;
}

.detail_item {
    margin: 0 0 1 1;
    padding: 0 1;
    color: $base0;
    background: transparent;
    height: auto;
}

.detail_item:hover {
    color: $base1;
    background: $base02;
}

/* === BUTTONS === */
#button_container {
    align: center middle;
    height: auto;
    margin: 0;
    padding: 2 0;
}

#back_button {
    background: $blue;
    color: $base3;
    width: 30;
    height: 3;
    text-style: bold;
}

#back_button:hover {
    background: $cyan;
}

#back_button:focus {
    background: $cyan;
    border: thick $cyan;
}

Button:focus {
    border: thick $blue;
}

/* === SCROLLABLE CONTAINERS === */
ScrollableContainer {
    background: transparent;
    scrollbar-background: $base02;
    scrollbar-color: $base01;
    scrollbar-color-hover: $blue;
    scrollbar-color-active: $cyan;
    padding: 0;
    margin: 0;
    border: none;
}

/* === CONNECTION STATUS INDICATORS === */
.status-ESTABLISHED {
    color: $green;
    text-style: bold;
}

.status-LISTEN {
    color: $blue;
    text-style: bold;
}

.status-TIME_WAIT {
    color: $yellow;
}

.status-CLOSE_WAIT {
    color: $red;
}
"""
