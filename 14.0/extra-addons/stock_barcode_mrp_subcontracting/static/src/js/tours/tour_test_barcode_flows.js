odoo.define('test_barcode_subcontract_flows.tour', function (require) {
'use strict';

var core = require('web.core');
var tour = require('web_tour.tour');

var _t = core._t;

// ----------------------------------------------------------------------------
// Tours
// ----------------------------------------------------------------------------

tour.register('test_receipt_subcontracted_1', {test: true}, [
    {
        trigger: '.o_barcode_client_action',
        run: 'scan product_subcontracted',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan LOC-01-01-00',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan product_subcontracted',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan LOC-01-02-00',
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan O-BTN.validate',
    },

    {
        trigger: '.o_notification.bg-success',
    },

]);

tour.register('test_receipt_subcontracted_2', {test: true}, [
    {
        trigger: '.o_barcode_client_action',
        run: 'scan product_subcontracted',
    },

    {
        trigger: ".o_field_widget[name=qty_producing]",
        position: "right",
        run: "text 1",
    },

    {
        trigger: ".modal-footer .btn-secondary[name=do_produce]",
        content: _t('Save'),
        position: "bottom",
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan O-BTN.record-components',
    },

    {
        trigger: ".o_field_widget[name=qty_producing]",
        position: "right",
        run: "text 1",
    },

    {
        trigger: ".modal-footer .btn-primary[name=continue_production]",
        position: "bottom",
    },

    {
        trigger: ".modal-footer .btn-primary[name=do_produce]",
        position: "bottom",
    },

    {
        trigger: '.o_barcode_client_action',
        run: 'scan O-BTN.validate',
    },

    {
        trigger: '.o_notification.bg-success',
    },

]);


});
