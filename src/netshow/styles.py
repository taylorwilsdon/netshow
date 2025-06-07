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

$accent_primary: $blue;
$accent_secondary: $magenta;
$accent_tertiary: $cyan;
$accent_success: $green;
$accent_warning: $yellow;
$accent_error: $red;

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
}

Footer {
    background: $bg_1;
    color: $fg_1;
    border-top: solid $blue;
}

/* === STATUS BAR === */
#stats_container {
    height: auto;
    margin: 1 0;
}

#status_bar {
    background: $bg_2;
    color: $fg_1;
    height: 3;
    padding: 0 2;
    border: solid $dim_0;
    margin: 0 1;
    text-style: bold;
}

/* === LAYOUT CONTAINERS === */
Vertical {
    width: 100%;
    height: 1fr;
    padding: 0 1;
}

/* === DATA TABLE STYLING === */
DataTable {
    background: $bg_0;
    color: $fg_0;
    width: 100%;
    height: 1fr;
    border: solid $dim_0;
    margin: 1 0;
}

DataTable .header {
    background: $bg_1;
    color: $fg_1;
    text-style: bold;
    height: 3;
    border-bottom: solid $blue;
}

DataTable .datatable--cursor {
    background: $blue;
    color: $bg_0;
    text-style: bold;
}

DataTable .datatable--hover {
    background: $bg_2;
    color: $fg_1;
}

DataTable:focus .datatable--cursor {
    background: $br_blue;
    text-style: bold;
}

/* === DETAIL SCREEN STYLING === */
#detail_title {
    background: $bg_2;
    color: $fg_1;
    height: 4;
    padding: 1 2;
    text-align: center;
    text-style: bold;
    margin: 1 0 2 0;
    border: solid $blue;
}

#main_content {
    height: auto;
    margin: 0 2;
}

#connection_details, #process_info {
    background: $bg_1;
    padding: 2;
    margin: 0 1 2 0;
    border: solid $dim_0;
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
    height: 3;
    border: solid $cyan;
}

.detail_title {
    margin: 0 0 1 0;
    padding: 0 1;
    color: $fg_1;
    text-style: bold;
    border-bottom: solid $cyan;
}

.detail_item {
    margin: 0 0 1 0;
    padding: 0 1;
    color: $fg_0;
    border-left: solid $cyan;
    padding-left: 2;
}

.detail_item:hover {
    color: $fg_1;
    background: $bg_2;
}

/* === BUTTONS === */
#button_container {
    align: center middle;
    height: auto;
    margin: 2 0;
}

#back_button {
    background: $blue;
    color: $bg_0;
    border: solid $blue;
    width: 25;
    height: 3;
    text-style: bold;
}

#back_button:hover {
    background: $br_blue;
    border: solid $br_blue;
}

#back_button:focus {
    background: $cyan;
    border: solid $cyan;
}

Button:focus {
    border: solid $blue;
}

/* === SCROLLABLE CONTAINERS === */
ScrollableContainer {
    background: transparent;
    scrollbar-background: $bg_1;
    scrollbar-color: $blue;
    scrollbar-color-hover: $br_blue;
    scrollbar-color-active: $cyan;
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
    outline: solid $blue;
}
"""
