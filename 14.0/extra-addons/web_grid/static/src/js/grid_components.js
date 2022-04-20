odoo.define('web_grid.components', function (require) {
    "use strict";

    const fieldUtils = require('web.field_utils');
    const utils = require('web.utils');

    const { useRef, useState } = owl.hooks;


    class BaseGridComponent extends owl.Component {
        constructor() {
            super(...arguments);
            this.currentInput = useRef("currentInput");
            this.state = useState({
                error: false,
            });
        }
        willUpdateProps(nextProps) {
            if (nextProps.date !== this.props.date) {
                // if we change the range of dates we are looking at, the
                // component must remove it's error state
                this.state.error = false;
            }
        }
        patched() {
            if (this.currentInput.el) {
                this.currentInput.el.select();
            }
        }

        //----------------------------------------------------------------------
        // Getters
        //----------------------------------------------------------------------

        /**
         * Returns the additional options needed for format/parse.
         * Override this getter to add options.
         *
         * @returns {Object}
         */
        get fieldOptions() {
            return this.props.nodeOptions;
        }
        /**
         * Returns the formatType needed for the format/parse function.
         * Override this getter to add options.
         *
         * @returns {Object}
         */
        get formatType() {
            return this.constructor.formatType || this.props.fieldInfo.type;
        }

        //----------------------------------------------------------------------
        // Private
        //----------------------------------------------------------------------

        /**
         * @private
         * @param {any} value
         * @returns {string}
         */
        _format(value) {
            return fieldUtils.format[this.formatType](value, {}, this.fieldOptions);
        }
        /**
         * @private
         * @param {any} value
         * @returns {string}
         */
        _parse(value) {
            return fieldUtils.parse[this.formatType](value, {}, this.fieldOptions);
        }

        //----------------------------------------------------------------------
        // Handlers
        //----------------------------------------------------------------------

        /**
         * This handler verifies that the value has a good format, if it is
         * the case it will trigger an event to update the value in DB.
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onBlurCell(ev) {
            let value;
            try {
                value = this._parse(ev.target.value);
                this.state.error = false;
            } catch (_) {
                this.state.error = ev.target.value;
            } finally {
                this.trigger('grid-cell-update', {
                    path: this.props.path,
                    value
                });
            }
        }
        /**
         * This handler notifies the grid that a cell has been focused
         *
         * @private
         */
        _onFocusCell() {
            this.trigger('grid-cell-focus', {
                path: this.props.path
            });
        }
    }
    BaseGridComponent.defaultProps = {
        cellHeight: 0,
        cellValue: 0,
        hasBarChartTotal: false,
        readonly: false,
        isTotal: false,
        nodeOptions: {}
    };
    BaseGridComponent.props = {
        cellHeight: {
            type: Number,
            optional: true
        },
        cellValue: {
            type: Number,
            optional: true
        },
        fieldInfo: Object,
        hasBarChartTotal: Boolean,
        isInput: Boolean,
        nodeOptions: Object,
        path: {
            type: String,
            optional: true
        },
        readonly: Boolean,
        isTotal: {
            type: Boolean,
            optional: true
        },
        date: {
            type: String,
            optional: true
        },
    };
    BaseGridComponent.template = 'web_grid.BaseGridComponent';
    BaseGridComponent.formatType = 'float_factor';


    class FloatFactorComponent extends BaseGridComponent {}


    class FloatTimeComponent extends BaseGridComponent {
        get fieldOptions() {
            return Object.assign({}, super.fieldOptions, {
                noLeadingZeroHour: true,
            });
        }
    }
    FloatTimeComponent.formatType = 'float_time';


    class FloatToggleComponent extends BaseGridComponent {
        constructor() {
            super(...arguments);
            this.state = useState({
                disabled: false,
                value: this.initialValue,
            });
        }
        willUpdateProps(nextProps) {
            if (nextProps.cellValue !== this.initialValue) {
                this.state.value = nextProps.cellValue;
            }
        }

        //----------------------------------------------------------------------
        // Getters
        //----------------------------------------------------------------------

        /**
         * Returns the additional options to the format function.
         *
         * @returns {Object}
         */
        get fieldOptions() {
            const fieldOptions = Object.assign({}, this.props.nodeOptions);
            if (!fieldOptions.factor) {
                fieldOptions.factor = 1;
            }
            const range = [0.0, 0.5, 1.0];
            if (!fieldOptions.range) {
                fieldOptions.range = range;
            }
            return fieldOptions;
        }
        /**
         * Returns the initial value.
         *
         * @returns {Number}
         */
        get initialValue() {
            return this.props.cellValue;
        }

        //----------------------------------------------------------------------
        // Handlers
        //----------------------------------------------------------------------

        /**
         * This handler is called when a user blurs the button
         * if the value in the cell has changed, it will trigger an event
         * to update the value in database. it will also disable the button as
         * long as the callbackfunction is not called.
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onBlurButton() {
            if (this.state.value !== this.initialValue) {
                this.state.disabled = true;
                this.trigger('grid-cell-update', {
                    path: this.props.path,
                    value: this.state.value,
                    doneCallback: () => {
                        this.state.disabled = false;
                    }
                });
            }
        }
        /**
         * This handler is called when a user clicks on a button
         * it will change the value in the state
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onClickButton() {
            const range = this.fieldOptions.range;
            const currentFloat = parseFloat(this._format(this.state.value));
            const closest = utils.closestNumber(currentFloat, range);
            const closestIndex = range.indexOf(closest);
            const nextIndex = closestIndex + 1 < range.length ? closestIndex + 1 : 0;
            this.state.value = this._parse(range[nextIndex].toString());
            this.trigger('grid-cell-update-temporary', {
                path: this.props.path,
                value: this.state.value
            });
        }

    }
    FloatToggleComponent.template = 'web_grid.FloatToggleComponent';


    return {
        BaseGridComponent,
        FloatFactorComponent,
        FloatTimeComponent,
        FloatToggleComponent,
    };
});
