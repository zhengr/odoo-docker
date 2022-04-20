odoo.define("documents_spreadsheet.SpreadsheetName", function (require) {
    "use strict";
    const { useState, useRef } = owl.hooks;

    const WIDTH_MARGIN = 3
    const PADDING_RIGHT = 5;
    const PADDING_LEFT = PADDING_RIGHT - WIDTH_MARGIN;


    class SpreadsheetName extends owl.Component {

        constructor() {
            super(...arguments);
            this.placeholder = this.env._t("Untitled spreadsheet");
            this.state = useState({
                inputSize: 1,
                isUntitled: this._isUntitled(this.props.name),
            });
            this.input = useRef("speadsheetNameInput");
        }

        /**
         * @override
         */
        async mounted() {
            this._setInputSize(this.props.name);
        }

        /**
         * @private
         * @param {string} text in the input element
         */
        _setInputSize(text) {
            const { font } = window.getComputedStyle(this.input.el);
            this.state.inputSize = this._computeTextWidth(text || this.placeholder, font) + PADDING_RIGHT + PADDING_LEFT;
        }

        /**
         * Return the width in pixels of a text with the given font.
         * @private
         * @param {string} text
         * @param {string} font css font attribute value
         * @returns {number} width in pixels
         */
        _computeTextWidth(text, font) {
            const canvas = document.createElement("canvas");
            const context = canvas.getContext("2d");
            context.font = font;
            const width = context.measureText(text).width;
            // add a small extra margin, otherwise the text jitters in
            // the input because it overflows very slightly for some
            // letters (?).
            return Math.ceil(width) + WIDTH_MARGIN;
        }

        /**
         * Check if the name is empty or is the generic name
         * for untitled spreadsheets.
         * @param {string} name
         * @returns {boolean}
         */
        _isUntitled(name) {
            name = name.trim();
            return !name || name === this.placeholder;
        }

        /**
         * @private
         * @param {InputEvent} ev
         */
        _onFocus(ev) {
            if (this._isUntitled(ev.target.value)) {
                ev.target.value = this.placeholder;
                ev.target.select();
            }
        }

        /**
         * @private
         * @param {InputEvent} ev
         */
        _onInput(ev) {
            const value = ev.target.value;
            this.state.isUntitled = this._isUntitled(value);
            this._setInputSize(value);
        }

        /**
         * @private
         * @param {InputEvent} ev
         */
        _onNameChanged(ev) {
            const value = ev.target.value.trim();
            ev.target.value = value;
            this._setInputSize(value);
            this.trigger("spreadsheet-name-changed", {
                name: value,
            });
            ev.target.blur();
        }
    }

    SpreadsheetName.template = "documents_spreadsheet.SpreadsheetName";
    SpreadsheetName.props = {
        name: String,
    };

    return SpreadsheetName;
});
