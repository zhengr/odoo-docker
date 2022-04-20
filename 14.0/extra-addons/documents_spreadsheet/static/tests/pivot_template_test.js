odoo.define("documents_spreadsheet.spreadsheet_template_tests", function (require) {
    "use strict";

    const pivotUtils = require("documents_spreadsheet.pivot_utils");
    const spreadsheetUtils = require("documents_spreadsheet.test_utils");
    const testUtils = require("web.test_utils");
    const DocumentsKanbanView = require("documents_spreadsheet.KanbanView");
    const DocumentsListView = require("documents_spreadsheet.ListView");
    const TemplateListView = require("documents_spreadsheet.TemplateListView");
    const { afterEach, beforeEach } = require('mail/static/src/utils/test_utils.js');

    const { nextTick, dom, fields, createActionManager, createView } = testUtils;
    const { createDocumentsView } = require("documents.test_utils");

    const { createSpreadsheetFromPivot, mockRPCFn } = spreadsheetUtils;


    const spreadsheet = require("documents_spreadsheet.spreadsheet_extended");
    const topbarMenuRegistry = spreadsheet.registries.topbarMenuRegistry;
    const { parse, astToFormula } = spreadsheet;

    async function convertFormula(config) {
        const [actionManager, model, env] = await createSpreadsheetFromPivot({
            model: "partner",
            data: config.data,
            arch: config.arch,
            mockRPC: mockRPCFn,
        });
        const { pivots } = model.exportData();
        const spreadsheetAction = actionManager.getCurrentController().widget;
        await Promise.all(
            Object.values(pivots).map((pivot) =>
                pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
            )
        );
        const ast = config.convertFunction(parse(config.formula), pivots);
        actionManager.destroy();
        return astToFormula(ast);
    }

    QUnit.module(
        "Spreadsheet",
        {
            beforeEach: function () {
                beforeEach(this);
                Object.assign(this.data, {
                    "documents.document": {
                        fields: {
                            name: { string: "Name", type: "char" },
                            raw: { string: "Data", type: "text" },
                            mimetype: { string: "mimetype", type: "char" },
                            handler: { string: "handler", type: "char" },
                            available_rule_ids: {
                                string: "Rules",
                                type: "many2many",
                                relation: "documents.workflow.rule",
                            },
                            folder_id: {
                                string: "Workspaces",
                                type: "many2one",
                                relation: "documents.folder",
                            },
                            res_model: { string: "Resource model", type: "char" },
                            tag_ids: {
                                string: "Tags",
                                type: "many2many",
                                relation: "documents.tag",
                            },
                            favorited_ids: { string: "Name", type: "many2many" },
                            is_favorited: { string: "Name", type: "boolean" },
                        },
                        records: [
                            { id: 1, name: "My spreadsheet", raw: "{}", is_favorited: false },
                            { id: 2, name: "", raw: "{}", is_favorited: true },
                        ],
                    },
                    "documents.workflow.rule": {
                        fields: {
                            display_name: { string: "Name", type: "char" },
                        },
                        records: [],
                    },
                    "documents.folder": {
                        fields: {
                            name: { string: "Name", type: "char" },
                            parent_folder_id: {
                                string: "Parent Workspace",
                                type: "many2one",
                                relation: "documents.folder",
                            },
                            description: { string: "Description", type: "text" },
                        },
                        records: [
                            {
                                id: 1,
                                name: "Workspace1",
                                description: "Workspace",
                                parent_folder_id: false,
                            },
                        ],
                    },
                    "documents.tag": {
                        fields: {},
                        records: [],
                        get_tags: () => [],
                    },
                    "spreadsheet.template": {
                        fields: {
                            name: { string: "Name", type: "char" },
                            data: { string: "Data", type: "binary" },
                        },
                        records: [
                            { id: 1, name: "Template 1", data: btoa("{}") },
                            { id: 2, name: "Template 2", data: btoa("{}") },
                        ],
                    },
                    partner: {
                        fields: {
                            foo: {
                                string: "Foo",
                                type: "integer",
                                searchable: true,
                                group_operator: "sum",
                            },
                            bar: {
                                string: "Bar",
                                type: "integer",
                                searchable: true,
                                group_operator: "sum",
                            },
                            probability: {
                                string: "Probability",
                                type: "integer",
                                searchable: true,
                                group_operator: "avg",
                            },
                            product_id: {
                                string: "Product",
                                type: "many2one",
                                relation: "product",
                                store: true,
                            },
                        },
                        records: [
                            {
                                id: 1,
                                foo: 12,
                                bar: 110,
                                probability: 10,
                                product_id: [37],
                            },
                            {
                                id: 2,
                                foo: 1,
                                bar: 110,
                                probability: 11,
                                product_id: [41],
                            },
                        ],
                    },
                    product: {
                        fields: {
                            name: { string: "Product Name", type: "char" },
                        },
                        records: [
                            {
                                id: 37,
                                display_name: "xphone",
                            },
                            {
                                id: 41,
                                display_name: "xpad",
                            },
                        ],
                    },
                });
            },
            afterEach() {
                afterEach(this);
            },
        },
        function () {
            QUnit.module("Template");
            QUnit.test("Don't change formula if not many2one", async function (assert) {
                assert.expect(1);
                const formula = `PIVOT("1","probability","foo","12","bar","110")`;
                const result = await convertFormula({
                    data: this.data,
                    formula,
                    convertFunction: pivotUtils.absoluteToRelative,
                    arch: `
                    <pivot string="Partners">
                        <field name="foo" type="col"/>
                        <field name="bar" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                });
                assert.equal(result, formula);
            });

            QUnit.test(
                "Adapt formula from absolute to relative with many2one in col",
                async function (assert) {
                    assert.expect(4);
                    const arch = `
                        <pivot string="Partners">
                            <field name="product_id" type="col"/>
                            <field name="bar" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`;

                    let result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT("1","probability","product_id","37","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`
                    );

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT.HEADER("1","product_id","37","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`
                    );

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT("1","probability","product_id","41","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`
                    );

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT.HEADER("1","product_id","41","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`
                    );
                }
            );

            QUnit.test("Adapt formula from absolute to relative with integer ids", async function (
                assert
            ) {
                assert.expect(2);
                const arch = `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`;

                let result = await convertFormula({
                    data: this.data,
                    arch,
                    formula: `PIVOT("1","probability","product_id",37,"bar","110")`,
                    convertFunction: pivotUtils.absoluteToRelative,
                });
                assert.equal(
                    result,
                    `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`
                );
                result = await convertFormula({
                    data: this.data,
                    arch,
                    formula: `PIVOT.HEADER("1","product_id",41,"bar","110")`,
                    convertFunction: pivotUtils.absoluteToRelative,
                });
                assert.equal(
                    result,
                    `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`
                );
            });

            QUnit.test(
                "Adapt formula from absolute to relative with many2one in row",
                async function (assert) {
                    assert.expect(4);
                    const arch = `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`;

                    let result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT("1","probability","product_id","37","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`
                    );

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT("1","probability","product_id","41","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`
                    );

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT("1","probability","product_id","41","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`
                    );

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT.HEADER("1","product_id","41","bar","110")`,
                        convertFunction: pivotUtils.absoluteToRelative,
                    });
                    assert.equal(
                        result,
                        `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`
                    );
                }
            );

            QUnit.test(
                "Adapt formula from relative to absolute with many2one in col",
                async function (assert) {
                    assert.expect(4);
                    const arch = `
                        <pivot string="Partners">
                            <field name="product_id" type="col"/>
                            <field name="bar" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`;

                    let result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 1),"bar","110")`,
                        convertFunction: pivotUtils.relativeToAbsolute,
                    });
                    assert.equal(result, `PIVOT("1","probability","product_id","37","bar","110")`);

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`,
                        convertFunction: pivotUtils.relativeToAbsolute,
                    });
                    assert.equal(result, `PIVOT.HEADER("1","product_id","37","bar","110")`);

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 2),"bar","110")`,
                        convertFunction: pivotUtils.relativeToAbsolute,
                    });
                    assert.equal(result, `PIVOT("1","probability","product_id","41","bar","110")`);

                    result = await convertFormula({
                        data: this.data,
                        arch,
                        formula: `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id", 2),"bar","110")`,
                        convertFunction: pivotUtils.relativeToAbsolute,
                    });
                    assert.equal(result, `PIVOT.HEADER("1","product_id","41","bar","110")`);
                }
            );

            QUnit.test("Template data does not contain pivot cache", async function (assert) {
                assert.expect(3);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const { pivots, sheets } = model.exportData();
                await pivotUtils.convertPivotFormulas(
                    env.services.rpc,
                    [sheets[0].cells.B3],
                    pivotUtils.relativeToAbsolute,
                    pivots
                );
                const pivotStates = Object.values(pivots).map((pivot) => [
                    pivot.cache,
                    pivot.isLoaded,
                    pivot.lastUpdate,
                ]);
                for (const [cache, isLoaded, last] of pivotStates) {
                    assert.equal(cache, undefined);
                    assert.equal(isLoaded, false);
                    assert.equal(last, undefined);
                }
                actionManager.destroy();
            });

            QUnit.test("Will convert additional template position to id -1", async function (
                assert
            ) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: async function (route, args) {
                        if (args.method === "search_read" && args.model === "ir.model") {
                            return [{ name: "partner" }];
                        } else if (
                            args.method === "read" &&
                            args.model === "spreadsheet.template"
                        ) {
                            return [{ data: btoa(JSON.stringify(model.exportData())) }];
                        }
                        return this._super.apply(this, arguments);
                    },
                });
                const { pivots } = model.exportData();
                const spreadsheetAction = actionManager.getCurrentController().widget;
                await Promise.all(
                    Object.values(pivots).map((pivot) =>
                        pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
                    )
                );
                model.dispatch("SET_VALUE", {
                    xc: "A1",
                    text: `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999),"bar","110")`,
                });
                const data = await pivotUtils.getDataFromTemplate(
                    env.services.rpc,
                    "this is a fake id"
                );
                assert.notOk(data.sheets[0].cells.A1.content);
                actionManager.destroy();
            });

            QUnit.test(
                "Adapt formula from relative to absolute with many2one in row",
                async function (assert) {
                    assert.expect(4);
                    const arch = `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`;

                    let result = await convertFormula({
                        formula: `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`,
                        data: this.data,
                        convertFunction: pivotUtils.relativeToAbsolute,
                        arch,
                    });
                    assert.equal(result, `PIVOT("1","probability","product_id","37","bar","110")`);

                    result = await convertFormula({
                        formula: `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`,
                        data: this.data,
                        convertFunction: pivotUtils.relativeToAbsolute,
                        arch,
                    });
                    assert.equal(result, `PIVOT.HEADER("1","product_id","37","bar","110")`);

                    result = await convertFormula({
                        formula: `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`,
                        data: this.data,
                        convertFunction: pivotUtils.relativeToAbsolute,
                        arch,
                    });
                    assert.equal(result, `PIVOT("1","probability","product_id","41","bar","110")`);

                    result = await convertFormula({
                        formula: `PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`,
                        data: this.data,
                        convertFunction: pivotUtils.relativeToAbsolute,
                        arch,
                    });
                    assert.equal(result, `PIVOT.HEADER("1","product_id","41","bar","110")`);
                }
            );

            QUnit.test("Adapt pivot as function arg from relative to absolute", async function (
                assert
            ) {
                assert.expect(1);
                const result = await convertFormula({
                    formula: `SUM(
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110"),
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")
                    )`,
                    data: this.data,
                    convertFunction: pivotUtils.relativeToAbsolute,
                    arch: `
                    <pivot string="Partners">
                        <field name="bar" type="col"/>
                        <field name="product_id" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                });
                assert.equal(
                    result,
                    `SUM(PIVOT("1","probability","product_id","37","bar","110"),PIVOT("1","probability","product_id","41","bar","110"))`
                );
            });

            QUnit.test("Adapt pivot as operator arg from relative to absolute", async function (
                assert
            ) {
                assert.expect(1);
                const result = await convertFormula({
                    formula: `
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")
                        +
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")
                    `,
                    data: this.data,
                    convertFunction: pivotUtils.relativeToAbsolute,
                    arch: `
                    <pivot string="Partners">
                        <field name="bar" type="col"/>
                        <field name="product_id" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                });
                assert.equal(
                    result,
                    `PIVOT("1","probability","product_id","37","bar","110")+PIVOT("1","probability","product_id","41","bar","110")`
                );
            });

            QUnit.test(
                "Adapt pivot as unary operator arg from relative to absolute",
                async function (assert) {
                    assert.expect(1);
                    const result = await convertFormula({
                        formula: `
                            -PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")
                        `,
                        data: this.data,
                        convertFunction: pivotUtils.relativeToAbsolute,
                        arch: `
                    <pivot string="Partners">
                        <field name="bar" type="col"/>
                        <field name="product_id" type="row"/>
                        <field name="probability" type="measure"/>
                    </pivot>`,
                    });
                    assert.equal(result, `-PIVOT("1","probability","product_id","37","bar","110")`);
                }
            );

            QUnit.test("Adapt pivot as operator arg from absolute to relative", async function (
                assert
            ) {
                assert.expect(1);
                const result = await convertFormula({
                    formula: `
                        PIVOT("1","probability","product_id","37","bar","110")
                        +
                        PIVOT("1","probability","product_id","41","bar","110")
                    `,
                    data: this.data,
                    convertFunction: pivotUtils.absoluteToRelative,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                });
                assert.equal(
                    result,
                    `PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")+PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110")`
                );
            });

            QUnit.test(
                "Adapt pivot as unary operator arg from absolute to relative",
                async function (assert) {
                    assert.expect(1);
                    const result = await convertFormula({
                        formula: `
                        -PIVOT("1","probability","product_id","37","bar","110")
                    `,
                        data: this.data,
                        convertFunction: pivotUtils.absoluteToRelative,
                        arch: `
                            <pivot string="Partners">
                                <field name="bar" type="col"/>
                                <field name="product_id" type="row"/>
                                <field name="probability" type="measure"/>
                            </pivot>`,
                    });
                    assert.equal(
                        result,
                        `-PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`
                    );
                }
            );

            QUnit.test("Adapt pivot as function arg from absolute to relative", async function (
                assert
            ) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const { pivots } = model.exportData();
                const spreadsheetAction = actionManager.getCurrentController().widget;
                await Promise.all(
                    Object.values(pivots).map((pivot) =>
                        pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
                    )
                );
                let ast = parse(`
                    SUM(
                        PIVOT("1","probability","product_id","37","bar","110"),
                        PIVOT("1","probability","product_id","41","bar","110")
                    )
                `);
                ast = pivotUtils.absoluteToRelative(ast, pivots);
                assert.equal(
                    astToFormula(ast),
                    `SUM(PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110"),PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",2),"bar","110"))`
                );

                actionManager.destroy();
            });

            QUnit.test("Computed ids are not changed", async function (assert) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const { pivots } = model.exportData();
                const spreadsheetAction = actionManager.getCurrentController().widget;
                await Promise.all(
                    Object.values(pivots).map((pivot) =>
                        pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
                    )
                );
                let ast = parse(`PIVOT("1","probability","product_id",A2,"bar","110")`);
                ast = pivotUtils.absoluteToRelative(ast, pivots);
                assert.equal(
                    astToFormula(ast),
                    `PIVOT("1","probability","product_id",A2,"bar","110")`
                );

                actionManager.destroy();
            });

            QUnit.test("Save as template menu", async function (assert) {
                assert.expect(7);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                    intercepts: {
                        do_action: function (ev) {
                            assert.step("create_template_wizard");
                            assert.equal(
                                ev.data.action,
                                "documents_spreadsheet.save_spreadsheet_template_action"
                            );
                            const context = ev.data.options.additional_context;
                            const data = JSON.parse(atob(context.default_data));
                            const name = context.default_template_name;
                            const cells = data.sheets[0].cells;
                            assert.equal(
                                name,
                                "pivot spreadsheet - Template",
                                "It should be named after the spreadsheet"
                            );
                            assert.ok(context.default_thumbnail);
                            assert.equal(
                                cells.A3.content,
                                `=PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",1))`
                            );
                            assert.equal(
                                cells.B3.content,
                                `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id",1),"bar","110")`
                            );
                        },
                    },
                });
                const file = topbarMenuRegistry.getAll().find((item) => item.id === "file");
                const saveAsTemplate = file.children.find((item) => item.id === "save_as_template");
                saveAsTemplate.action(env);
                await nextTick();
                assert.verifySteps(["create_template_wizard"]);
                actionManager.destroy();
            });

            QUnit.test("Autofill template position", async function (assert) {
                assert.expect(4);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                model.dispatch("SET_VALUE", {
                    xc: "B2",
                    text: `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999),"bar",PIVOT.POSITION("1","bar", 4444))`,
                });

                function selectB2(model) {
                    model.dispatch("SET_SELECTION", {
                        anchor: [1, 1],
                        zones: [{ top: 1, bottom: 1, right: 1, left: 1 }],
                    });
                }

                // DOWN
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 2 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(1, 2).content,
                    `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 10000),"bar",PIVOT.POSITION("1","bar", 4444))`
                );

                // UP
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 0 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(1, 0).content,
                    `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9998),"bar",PIVOT.POSITION("1","bar", 4444))`
                );

                // RIGHT
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 2, row: 1 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(2, 1).content,
                    `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999),"bar",PIVOT.POSITION("1","bar", 4445))`
                );

                // LEFT
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 0, row: 1 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(0, 1).content,
                    `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999),"bar",PIVOT.POSITION("1","bar", 4443))`
                );

                actionManager.destroy();
            });

            QUnit.test("Autofill template position: =-PIVOT(...)", async function (assert) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                model.dispatch("SET_VALUE", {
                    xc: "B2",
                    text: `= - PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999),"bar",PIVOT.POSITION("1","bar", 4444))`,
                });

                // DOWN
                model.dispatch("SET_SELECTION", {
                    anchor: [1, 1],
                    zones: [{ top: 1, bottom: 1, right: 1, left: 1 }],
                });
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 2 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(1, 2).content,
                    `= - PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 10000),"bar",PIVOT.POSITION("1","bar", 4444))`
                );

                actionManager.destroy();
            });

            QUnit.test("Autofill template position: 2 PIVOT in one formula", async function (assert) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                model.dispatch("SET_VALUE", {
                    xc: "B2",
                    text: `=SUM(
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999),"bar",PIVOT.POSITION("1","bar", 4444)),
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 666),"bar",PIVOT.POSITION("1","bar", 4444))
                    )`.replace(/\n/g, ""),
                });

                model.dispatch("SET_SELECTION", {
                    anchor: [1, 1],
                    zones: [{ top: 1, bottom: 1, right: 1, left: 1 }],
                });
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 2 });
                model.dispatch("AUTOFILL");
                // Well this does not work, it only updates the last PIVOT figure. But at least it does not crash.
                assert.equal(
                    model.getters.getCell(1, 2).content,
                    `=SUM(
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999),"bar",PIVOT.POSITION("1","bar", 4444)),
                        PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 667),"bar",PIVOT.POSITION("1","bar", 4444))
                    )`.replace(/\n/g, "")
                );

                actionManager.destroy();
            });

            QUnit.test("Autofill template position: PIVOT.POSITION not in PIVOT", async function (assert) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                model.dispatch("SET_VALUE", {
                    xc: "B2",
                    text: `=PIVOT.POSITION("1","foo", 3333)`,
                });
                function selectB2(model) {
                    model.dispatch("SET_SELECTION", {
                        anchor: [1, 1],
                        zones: [{ top: 1, bottom: 1, right: 1, left: 1 }],
                    });
                }

                // DOWN
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 2 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(1, 2).content,
                    `=PIVOT.POSITION("1","foo", 3333)`,
                    "Should have copied the origin value"
                );
                actionManager.destroy();
            });

            QUnit.test("Autofill template position: with invalid pivot id", async function (assert) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                model.dispatch("SET_VALUE", {
                    xc: "B2",
                    text: `=PIVOT("1","probability","product_id",PIVOT.POSITION("10000","product_id", 9999))`,
                });
                function selectB2(model) {
                    model.dispatch("SET_SELECTION", {
                        anchor: [1, 1],
                        zones: [{ top: 1, bottom: 1, right: 1, left: 1 }],
                    });
                }

                // DOWN
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 2 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(1, 2).content,
                    `=PIVOT("1","probability","product_id",PIVOT.POSITION("10000","product_id", 9999))`,
                    "Should have copied the origin value"
                );
                actionManager.destroy();
            });

            QUnit.test("Autofill template position: increment last group", async function (assert) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="foo" type="row"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                model.dispatch("SET_VALUE", {
                    xc: "B2",
                    text: `=PIVOT("1","probability","foo",PIVOT.POSITION("1","foo", 3333),"product_id",PIVOT.POSITION("1","product_id", 9999),"bar",PIVOT.POSITION("1","bar", 4444))`,
                });

                function selectB2(model) {
                    model.dispatch("SET_SELECTION", {
                        anchor: [1, 1],
                        zones: [{ top: 1, bottom: 1, right: 1, left: 1 }],
                    });
                }

                // DOWN
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 2 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(1, 2).content,
                    `=PIVOT("1","probability","foo",PIVOT.POSITION("1","foo", 3333),"product_id",PIVOT.POSITION("1","product_id", 10000),"bar",PIVOT.POSITION("1","bar", 4444))`,
                    "It should have incremented the last row group position"
                );
                actionManager.destroy();
            });

            QUnit.test("Autofill template position: does not increment last field if not many2one", async function (assert) {
                assert.expect(1);
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="foo" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                // last row field (foo) is not a position
                model.dispatch("SET_VALUE", {
                    xc: "B2",
                    text: `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999), "foo","10","bar","15")`,
                });

                function selectB2(model) {
                    model.dispatch("SET_SELECTION", {
                        anchor: [1, 1],
                        zones: [{ top: 1, bottom: 1, right: 1, left: 1 }],
                    });
                }

                // DOWN
                selectB2(model);
                model.dispatch("AUTOFILL_SELECT", { col: 1, row: 2 });
                model.dispatch("AUTOFILL");
                assert.equal(
                    model.getters.getCell(1, 2).content,
                    `=PIVOT("1","probability","product_id",PIVOT.POSITION("1","product_id", 9999), "foo","10","bar","15")`,
                    "It should not have changed the formula"
                );
                actionManager.destroy();
            });



            QUnit.module("Template Modal");

            QUnit.test("Create spreadsheet from kanban view opens a modal", async function (
                assert
            ) {
                assert.expect(2);
                const kanban = await createDocumentsView({
                    View: DocumentsKanbanView,
                    model: "documents.document",
                    data: this.data,
                    arch: `
                        <kanban><templates><t t-name="kanban-box">
                            <div>
                                <field name="name"/>
                            </div>
                        </t></templates></kanban>
                    `,
                    archs: {
                        "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                    },
                });
                await dom.click(".o_documents_kanban_spreadsheet");
                await nextTick();

                assert.ok(
                    $(".o-spreadsheet-templates-dialog").length,
                    "should have opened the template modal"
                );

                assert.ok(
                    $(".o-spreadsheet-templates-dialog .modal-body .o_searchview").length,
                    "The Modal should have a search view"
                );
                kanban.destroy();
            });

            QUnit.test("Create spreadsheet from list view opens a modal", async function (assert) {
                assert.expect(2);
                const list = await createDocumentsView({
                    View: DocumentsListView,
                    model: "documents.document",
                    data: this.data,
                    arch: `<tree></tree>`,
                    archs: {
                        "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                    },
                });
                await dom.click(".o_documents_kanban_spreadsheet");

                assert.ok(
                    $(".o-spreadsheet-templates-dialog").length,
                    "should have opened the template modal"
                );

                assert.ok(
                    $(".o-spreadsheet-templates-dialog .modal-body .o_searchview").length,
                    "The Modal should have a search view"
                );
                list.destroy();
            });

            QUnit.test("Can search template in modal with searchbar", async function (assert) {
                assert.expect(4);
                const kanban = await createDocumentsView({
                    View: DocumentsKanbanView,
                    model: "documents.document",
                    data: this.data,
                    arch: `
                        <kanban><templates><t t-name="kanban-box">
                            <field name="name"/>
                        </t></templates></kanban>
                    `,
                    archs: {
                        "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                    },
                });
                await dom.click(".o_documents_kanban_spreadsheet");
                const dialog = document.querySelector(".o-spreadsheet-templates-dialog");
                assert.equal(dialog.querySelectorAll(".o-template").length, 3);
                assert.equal(dialog.querySelector(".o-template").textContent, "Blank");

                const searchInput = dialog.querySelector(".o_searchview_input");
                await fields.editInput(searchInput, "Template 1");
                await dom.triggerEvent(searchInput, "keydown", { key: "Enter" });
                assert.equal(dialog.querySelectorAll(".o-template").length, 2);
                assert.equal(dialog.querySelector(".o-template").textContent, "Blank");
                kanban.destroy();
            });

            QUnit.test("Can create a spreadsheet from template", async function (assert) {
                assert.expect(5);
                const kanban = await createDocumentsView({
                    View: DocumentsKanbanView,
                    model: "documents.document",
                    data: this.data,
                    arch: `
                        <kanban><templates><t t-name="kanban-box">
                            <field name="name"/>
                        </t></templates></kanban>
                    `,
                    archs: {
                        "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                    },
                    mockRPC: function (route, args) {
                        if (args.method === "create" && args.model === "documents.document") {
                            assert.step("create_sheet");
                            assert.equal(
                                args.args[0].name,
                                "Template 2",
                                "It should have been named after the template"
                            );
                        }
                        if (args.method === "search_read" && args.model === "ir.model") {
                            return Promise.resolve([{ name: "partner" }]);
                        }
                        return this._super.apply(this, arguments);
                    },
                    intercepts: {
                        do_action: function (ev) {
                            assert.step("redirect");
                            assert.equal(ev.data.action.tag, "action_open_spreadsheet");
                        },
                    },
                });

                await dom.click(".o_documents_kanban_spreadsheet");
                const dialog = document.querySelector(".o-spreadsheet-templates-dialog");

                // select template 2
                await dom.triggerEvent(dialog.querySelectorAll(".o-template img")[2], "focus");
                await dom.click(dialog.querySelector(".o-spreadsheet-create"));
                assert.verifySteps(["create_sheet", "redirect"]);
                kanban.destroy();
            });

            QUnit.test("Will convert additional template position to empty cell", async function (
                assert
            ) {
                assert.expect(4);
                const data = Object.assign({}, this.data);
                // 1. create a spreadsheet with a pivot
                const [actionManager, model, env] = await createSpreadsheetFromPivot({
                    model: "partner",
                    data: this.data,
                    arch: `
                        <pivot string="Partners">
                            <field name="bar" type="col"/>
                            <field name="product_id" type="row"/>
                            <field name="probability" type="measure"/>
                        </pivot>`,
                    mockRPC: mockRPCFn,
                });
                const { pivots } = model.exportData();
                const spreadsheetAction = actionManager.getCurrentController().widget;
                await Promise.all(
                    Object.values(pivots).map((pivot) =>
                        pivotUtils.fetchCache(pivot, spreadsheetAction._rpc.bind(spreadsheetAction))
                    )
                );

                // 2. Set a template position which is too high
                model.dispatch("SET_VALUE", {
                    xc: "F1", // there are other pivot headers on row 1
                    text: `=PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",999),"bar","110")`,
                });
                model.dispatch("SET_VALUE", {
                    xc: "F15", // there are no other pivot headers on row 15
                    text: `=PIVOT.HEADER("1","product_id",PIVOT.POSITION("1","product_id",888),"bar","110")`,
                });
                model.dispatch("SET_VALUE", {
                    xc: "F16",
                    text: `Coucou petite perruche`,
                });
                const modelData = model.exportData();
                data["spreadsheet.template"].records.push({
                    id: 99,
                    name: "template",
                    data: btoa(JSON.stringify(modelData)),
                });
                actionManager.destroy();

                // 3. Create a spreadsheet from the template
                const kanban = await createDocumentsView({
                    View: DocumentsKanbanView,
                    model: "documents.document",
                    data,
                    arch: `
                        <kanban><templates><t t-name="kanban-box">
                            <field name="name"/>
                        </t></templates></kanban>
                    `,
                    archs: {
                        "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                    },
                    mockRPC: function (route, args) {
                        if (args.method === "create" && args.model === "documents.document") {
                            const data = JSON.parse(args.args[0].raw);
                            assert.step("create_sheet");
                            assert.equal(
                                data.sheets[0].cells.F15.content,
                                `Coucou petite perruche`,
                                "Row 15 should have been deleted"
                            );
                            assert.notOk(
                                data.sheets[0].cells.F1.content,
                                "The invalid F1 cell should be empty"
                            );
                        }
                        if (args.method === "search_read" && args.model === "ir.model") {
                            return Promise.resolve([{ name: "partner" }]);
                        }
                        return this._super.apply(this, arguments);
                    },
                });

                await dom.click(".o_documents_kanban_spreadsheet");
                const dialog = document.querySelector(".o-spreadsheet-templates-dialog");
                // select template 2
                await dom.triggerEvent(dialog.querySelectorAll(".o-template img")[3], "focus");
                await dom.click(dialog.querySelector(".o-spreadsheet-create"));
                assert.verifySteps(["create_sheet"]);
                kanban.destroy();
            });

            QUnit.test("Name template with spreadsheet name", async function (assert) {
                assert.expect(3);
                const actionManager = await createActionManager({
                    data: this.data,
                    mockRPC: function (route, args) {
                        if (args.method === "create" && args.model === "spreadsheet.template") {
                            assert.step("create_template");
                            assert.equal(
                                args.args[0].name,
                                "My spreadsheet",
                                "It should be named after the spreadsheet"
                            );
                        }
                        return this._super.apply(this, arguments);
                    },
                    intercepts: {
                        do_action: function (ev) {
                            assert.step("create_template_wizard");
                            const name = ev.data.options.additional_context.default_template_name;
                            assert.equal(
                                name,
                                "My spreadsheet - Template",
                                "It should be named after the spreadsheet"
                            );
                        },
                    },
                });
                await actionManager.doAction({
                    type: "ir.actions.client",
                    tag: "action_open_spreadsheet",
                    params: {
                        active_id: 2,
                    },
                });
                const input = actionManager.el.querySelector(".breadcrumb-item input");
                await fields.editInput(input, "My spreadsheet");
                await dom.triggerEvent(input, "change");
                const spreadSheetComponent = actionManager.getCurrentController().widget
                    .spreadsheetComponent.componentRef.comp;
                const file = topbarMenuRegistry.getAll().find((item) => item.id === "file");
                const saveAsTemplate = file.children.find((item) => item.id === "save_as_template");
                saveAsTemplate.action(spreadSheetComponent.env);
                await nextTick();

                assert.verifySteps(["create_template_wizard"]);
                actionManager.destroy();
            });

            QUnit.test("Can fetch next templates", async function (assert) {
                assert.expect(8);
                this.data["spreadsheet.template"].records = this.data[
                    "spreadsheet.template"
                ].records.concat([
                    { id: 3, name: "Template 3", data: btoa("{}") },
                    { id: 4, name: "Template 4", data: btoa("{}") },
                    { id: 5, name: "Template 5", data: btoa("{}") },
                    { id: 6, name: "Template 6", data: btoa("{}") },
                    { id: 7, name: "Template 7", data: btoa("{}") },
                    { id: 8, name: "Template 8", data: btoa("{}") },
                    { id: 9, name: "Template 9", data: btoa("{}") },
                    { id: 10, name: "Template 10", data: btoa("{}") },
                    { id: 11, name: "Template 11", data: btoa("{}") },
                    { id: 12, name: "Template 12", data: btoa("{}") },
                ]);
                let fetch = 0;
                const kanban = await createDocumentsView({
                    View: DocumentsKanbanView,
                    model: "documents.document",
                    data: this.data,
                    arch: `
                        <kanban><templates><t t-name="kanban-box">
                            <field name="name"/>
                        </t></templates></kanban>
                    `,
                    archs: {
                        "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                    },
                    mockRPC: function (route, args) {
                        if (
                            route === "/web/dataset/search_read" &&
                            args.model === "spreadsheet.template"
                        ) {
                            fetch++;
                            assert.equal(args.limit, 9);
                            assert.step("fetch_templates");
                            if (fetch === 1) {
                                assert.equal(args.offset, undefined);
                            } else if (fetch === 2) {
                                assert.equal(args.offset, 9);
                            }
                        }
                        if (args.method === "search_read" && args.model === "ir.model") {
                            return Promise.resolve([{ name: "partner" }]);
                        }
                        return this._super.apply(this, arguments);
                    },
                });

                await dom.click(".o_documents_kanban_spreadsheet");
                const dialog = document.querySelector(".o-spreadsheet-templates-dialog");

                assert.equal(dialog.querySelectorAll(".o-template").length, 10);
                await dom.click(dialog.querySelector(".o_pager_next"));
                assert.verifySteps(["fetch_templates", "fetch_templates"]);
                kanban.destroy();
            });

            QUnit.test("Disable create button if no template is selected", async function (assert) {
                assert.expect(2);
                this.data["spreadsheet.template"].records = this.data[
                    "spreadsheet.template"
                ].records.concat([
                    { id: 3, name: "Template 3", data: btoa("{}") },
                    { id: 4, name: "Template 4", data: btoa("{}") },
                    { id: 5, name: "Template 5", data: btoa("{}") },
                    { id: 6, name: "Template 6", data: btoa("{}") },
                    { id: 7, name: "Template 7", data: btoa("{}") },
                    { id: 8, name: "Template 8", data: btoa("{}") },
                    { id: 9, name: "Template 9", data: btoa("{}") },
                    { id: 10, name: "Template 10", data: btoa("{}") },
                    { id: 11, name: "Template 11", data: btoa("{}") },
                    { id: 12, name: "Template 12", data: btoa("{}") },
                ]);
                const kanban = await createDocumentsView({
                    View: DocumentsKanbanView,
                    model: "documents.document",
                    data: this.data,
                    arch: `
                        <kanban><templates><t t-name="kanban-box">
                            <field name="name"/>
                        </t></templates></kanban>
                    `,
                    archs: {
                        "spreadsheet.template,false,search": `<search><field name="name"/></search>`,
                    },
                    mockRPC: mockRPCFn,
                });
                // open template dialog
                await dom.click(".o_documents_kanban_spreadsheet");
                const dialog = document.querySelector(".o-spreadsheet-templates-dialog");

                // select template
                await dom.triggerEvent(dialog.querySelectorAll(".o-template img")[1], "focus");

                // change page; no template should be selected
                await dom.click(dialog.querySelector(".o_pager_next"));
                assert.containsNone(dialog, ".o-template-selected");
                const createButton = dialog.querySelector(".o-spreadsheet-create");
                await dom.click(createButton);
                assert.ok(createButton.attributes.disabled);
                kanban.destroy();
            });

            QUnit.test("Open spreadsheet template from list view", async function (assert) {
                assert.expect(3);
                const list = await createView({
                    View: TemplateListView,
                    model: "spreadsheet.template",
                    data: this.data,
                    arch: `
                        <tree>
                            <field name="name"/>
                            <button string="Edit" class="float-right" name="edit_template" icon="fa-pencil" />
                        </tree>
                    `,
                    intercepts: {
                        do_action: function ({ data }) {
                            assert.step("redirect_to_template");
                            assert.deepEqual(
                                data.action,
                                {
                                    type: "ir.actions.client",
                                    tag: "action_open_template",
                                    params: {
                                        active_id: 1,
                                        showFormulas: true,
                                    },
                                }
                            );
                        },
                    },
                });
                await dom.clickFirst(`button[name="edit_template"]`);
                assert.verifySteps(["redirect_to_template"]);
                list.destroy();
            });

            QUnit.test("Copy template from list view", async function (assert) {
                assert.expect(4);
                const list = await createView({
                    View: TemplateListView,
                    model: "spreadsheet.template",
                    data: this.data,
                    arch: `
                        <tree>
                            <field name="name"/>
                            <button string="Make a copy" class="float-right" name="copy" type="object" icon="fa-clone" />
                        </tree>
                    `,
                    intercepts: {
                        execute_action: function ({ data }) {
                            assert.strictEqual(data.action_data.name, 'copy',
                                "should call the copy method");
                            assert.equal(data.env.currentID, 1, "template with ID 1 should be copied")
                            assert.step("add_copy_of_template");
                        },
                    },
                });
                await dom.clickFirst(`button[name="copy"]`);
                assert.verifySteps(["add_copy_of_template"])
                list.destroy();
            });

            QUnit.test("Create new spreadsheet from template from list view", async function (assert) {
                assert.expect(4);
                const list = await createView({
                    View: TemplateListView,
                    model: "spreadsheet.template",
                    data: this.data,
                    arch: `
                        <tree>
                            <field name="name"/>
                            <button string="New spreadsheet" class="o-new-spreadsheet float-right" name="create_spreadsheet" icon="fa-plus" />
                        </tree>
                    `,
                    mockRPC: async function (route, args) {
                        if (args.method === "create" && args.model === "documents.document") {
                            assert.step("spreadsheet_created");
                            return 42;
                        }
                        return this._super.apply(this, arguments);
                    },
                    intercepts: {
                        do_action: function ({ data }) {
                            assert.deepEqual(data.action, {
                                type: "ir.actions.client",
                                tag: "action_open_spreadsheet",
                                params: {
                                    active_id: 42,
                                },
                            });
                            assert.step("redirect_to_spreadsheet");
                        },
                    },
                });
                await dom.clickFirst(`button[name="create_spreadsheet"]`);
                assert.verifySteps(["spreadsheet_created", "redirect_to_spreadsheet"])
                list.destroy();
            });
        }
    );
});
