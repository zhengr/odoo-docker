odoo.define('documents_spreadsheet_account.spreadsheet_template_sales_commission', function (require) {
    'use strict';

    require('web.dom_ready');
    const tour = require('web_tour.tour');

    const TEMPLATE_NAME = "Sales Commission";

    tour.register('spreadsheet_template_sales_commission', {
        test: true,
        url: '/web',
    }, [
        {
            trigger: '.o_app[data-menu-xmlid="documents.menu_root"]',
            content: 'Open document app',
            run: 'click',
        },
        {
            trigger: '.o_menu_header_lvl_1[data-menu-xmlid="documents.Config"]',
            content: 'Open Configuration menu',
            run: 'click',
        },
        {
            trigger: '.o_menu_entry_lvl_2[data-menu-xmlid="documents_spreadsheet.menu_technical_spreadsheet_template"]',
            content: 'Open Configuration menu',
            run: 'click',
        },
        {
            trigger: '.o_searchview .o_facet_remove',
            content: 'Remove "My templates" filter',
            run: 'click',
        },
        {
            trigger: 'input.o_searchview_input',
            content: 'Search the template',
            run: `text ${TEMPLATE_NAME}`,
        },
        {
            trigger: '.o_menu_item.o_selection_focus',
            content: 'Validate search',
            run: 'click',
        },
        {
            trigger: `tr.o_data_row:first-child td[title="${TEMPLATE_NAME}"]`,
            content: 'Wait search to complete',
        },
        {
            trigger: 'button.o-new-spreadsheet',
            content: 'Create spreadsheet from template',
            run: 'click',
        },
        {
            trigger: '.o-spreadsheet',
            content: 'Redirect to spreadsheet',
        },
    ]);
});
