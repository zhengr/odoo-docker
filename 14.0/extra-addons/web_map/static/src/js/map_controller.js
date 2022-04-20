odoo.define('web_map.MapController', function (require) {
"use strict";

const AbstractController = require('web.AbstractController');
const core = require('web.core');
const qweb = core.qweb;

const MapController = AbstractController.extend({
    custom_events: _.extend({}, AbstractController.prototype.custom_events, {
        'pin_clicked': '_onPinClick',
        'get_itinerary_clicked': '_onGetItineraryClicked',
        'open_clicked': '_onOpenClicked',
        'pager_changed': '_onPagerChanged',
        'coordinate_fetched': '_onCoordinateFetched',
    }),

    /**
     * @constructor
     */
    init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.actionName = params.actionName;
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     * @param {jQuery} [$node]
     */
    renderButtons: function ($node) {
        let url = 'https://www.google.com/maps/dir/?api=1';
        if (this.model.data.records.length) {
            const coordinates = this.model.data.records
                .filter(record => record.partner && record.partner.partner_latitude && record.partner.partner_longitude)
                .map(record => record.partner.partner_latitude + ',' + record.partner.partner_longitude);
            url += `&waypoints=${_.uniq(coordinates).join('|')}`;
        }
        this.$buttons = $(qweb.render("MapView.buttons"), { widget: this });
        this.$buttons.find('a').attr('href', url);
        if ($node) {
            this.$buttons.appendTo($node);
        }
    },
    /**
     * @override
     */
    update: async function () {
        await this._super(...arguments);
        this._updatePaging();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Return the params (currentMinimum, limit and size) to pass to the pager,
     * according to the current state.
     *
     * @private
     * @returns {Object}
     */
    _getPagingInfo: function () {
        const state = this.model.get();
        return {
            currentMinimum: state.offset + 1,
            limit: state.limit,
            size: state.count,
        };
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {OdooEvent} ev
     */
    _onCoordinateFetched: function (ev) {
        ev.stopPropagation();
        this.update({}, { reload: false });
    },
    /**
     * Redirects to google maps with all the records' coordinates.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onGetItineraryClicked: function (ev) {
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${ev.data.lat},${ev.data.lon}`);
    },
    /**
     * Redirects to views when clicked on open button in marker popup.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onOpenClicked: function (ev) {
        if (ev.data.ids.length > 1) {
            this.do_action({
                type: 'ir.actions.act_window',
                name: this.actionName,
                views: [[false, 'list'], [false, 'form']],
                res_model: this.modelName,
                domain: [['id', 'in', ev.data.ids]],
            });
        } else {
            this.trigger_up('switch_view', {
                view_type: 'form',
                res_id: ev.data.ids[0],
                mode: 'readonly',
                model: this.modelName
            });
        }
    },
    /**
     * @private
     * @param {OdooEvent} ev
     */
    async _onPagerChanged(ev) {
        const { currentMinimum, limit } = ev.data;
        await this.reload({ limit, offset: currentMinimum - 1 });
    },
});

return MapController;
});
