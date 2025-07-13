"""Styles for the NetshowApp - Enhanced Selenized Dark Theme."""

CSS = """
/* === SELENIZED DARK COLOR PALETTE === */
$bg_0: #103c48;
$bg_1: #184956;
$bg_2: #2d5b69;
$dim_0: #72898f;
$fg_0: #adbcbc;
$fg_1: #cad8d9;

$red: #fa5750;
$green: #75b938;
$yellow: #dbb32d;
$blue: #4695f7;
$magenta: #f275be;
$cyan: #41c7b9;
$orange: #ed8649;
$violet: #af88eb;

$br_red: #ff665c;
$br_green: #84c747;
$br_yellow: #ebc13d;
$br_blue: #58a3ff;
$br_magenta: #ff84cd;
$br_cyan: #53d6c7;
$br_orange: #fd9456;
$br_violet: #bd96fa;


/* === METRICS ROW === */
#metrics_row {
    height: 3;
    margin: 0;
    padding: 0 1;
}

.metric {
    background: $bg_1;
    color: $fg_1;
    border: solid $cyan;
    padding: 0 1;
    margin: 0;
    text-style: bold;
    text-align: center;
    width: 1fr;
    min-width: 15;
}

/* === SPECIFIC METRIC WIDTHS === */
#conn_metric {
    width: 2fr;
}

#active_metric {
    width: 1.1fr;
    min-width: 12;
}

#listen_metric {
    width: 1.3fr;
    min-width: 15;
}

#bandwidth_metric {
    width: 2.5fr;
    min-width: 25;
}

/* === FILTER CONTAINER === */
#filter_container {
    height: 3;
    margin: 0;
    padding: 0 1;
}

#filter_input {
    background: $bg_1;
    color: $fg_1;
    border: solid $magenta;
    height: 1;
    padding: 0 1;
}

#filter_input:focus {
    background: $bg_0;
    border: solid $br_cyan;
    color: $fg_1;
}


/* === GLOBAL STYLES === */
Screen {
    background: $bg_0;
    color: $fg_0;
}

/* === HEADER & FOOTER === */
Header {
    background: $bg_1;
    color: $fg_1;
    border-bottom: solid $blue;
    text-style: bold;
    height: 3;
}

Footer {
    background: $bg_1;
    color: $fg_1;
    height: 1;
}

/* === STATUS BAR === */
#stats_container {
    height: auto;
    margin: 0;
    border: solid $dim_0;
    padding: 0;
}

#status_bar {
    background: $bg_1;
    color: $fg_1;
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
    border-right: none;
}

#process_info {
    border-left: none;
}

/* === DATA TABLE STYLING === */
DataTable {
    background: $bg_0;
    color: $fg_0;
    width: 100%;
    height: 1fr;
    border: none;
    margin: 0;
}

#connections_table {
    border: none !important;
}

DataTable .header {
    background: $bg_1;
    color: $fg_1;
    text-style: bold;
    height: 1;
}

DataTable .datatable--cursor {
    background: $bg_2;
    color: $fg_1;
    text-style: bold;
}

DataTable .datatable--hover {
    background: $bg_1;
    color: $fg_1;
}

DataTable:focus .datatable--cursor {
    background: $dim_0;
    color: $fg_1;
    text-style: bold;
}

/* === DETAIL SCREEN STYLING === */
#detail_title {
    background: $bg_2;
    color: $fg_1;
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
}

#connection_details, #process_info {
    background: $bg_1;
    padding: 2;
    margin: 0;
    height: auto;
    width: 1fr;
}

.section_header {
    background: $bg_2;
    color: $fg_1;
    padding: 1 2;
    text-align: center;
    text-style: bold;
    margin: 0 0 1 0;
    height: 10;
}

.detail_title {
    margin: 0 0 1 0;
    padding: 1 1;
    color: $fg_1;
    text-style: bold;
    background: $bg_2;
}

.detail_item {
    margin: 0 0 1 1;
    padding: 0 1;
    color: $fg_1;
    background: transparent;
    height: auto;
}

.detail_item:hover {
    color: $fg_1;
    background: $bg_2;
    border-left: $br_blue;
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
    color: $bg_0;
    width: 30;
    height: 3;
    text-style: bold;
}

#back_button:hover {
    background: $br_blue;
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
    scrollbar-background: $bg_1;
    scrollbar-color: $blue;
    scrollbar-color-hover: $br_blue;
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

/* === ACCESSIBILITY === */
*:focus {
    outline: thick $blue;
}

.epic-glow {
    color: $br_blue;
    text-style: bold;
}
"""
