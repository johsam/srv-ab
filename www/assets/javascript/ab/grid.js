/*
 *  Created by: Johan S - 2017
 *
 */

// @flow

/* global Josa:true */

Ext.define('Josa.ab.grid', {
    extend: 'Ext.grid.Panel',
    alias: 'josa.ab.grid',

    viewConfig: {
        loadingText: 'Loading data...',
        stripeRows: true,
    },

    features: [
        {
            ftype: 'grouping',
            groupHeaderTpl: "({rows.length}) Books(s) with {groupField} '{groupValue}'",
        },
    ],

    plugins: [Ext.create('Ext.grid.plugin.CellEditing')],

    columnLines: true,
    border: false,

    config: {},

    abHilitePattern: undefined, // Regexp for highliting search patter in grid

    /*******************************************************************
     *
     * Handler -> onTextFieldChange
     *
     ******************************************************************/

    onTextFieldChange: function () {
        const textField = this.down('textfield[name=searchField]');
        this.delayUtil.delay(1000, this.delaytask, this, [{ store: this.getStore(), value: textField.getValue() }]);
    },

    /*******************************************************************
     *
     * Private delaytask
     *
     ******************************************************************/

    delaytask: function (cfg) {
        let abFilter;

        if (cfg.value !== '') {
            this.abHilitePattern = new RegExp('(' + cfg.value + ')', 'gi');
            this.store.clearFilter(true);

            abFilter = new RegExp(cfg.value, 'i');

            //    Filter on all columns

            this.store.filter(
                new Ext.util.Filter({
                    filterFn: function (object) {
                        let match = false;
                        Ext.Object.each(object.data, (_property, value) => {
                            match = match || abFilter.test(String(value));
                        });
                        return match;
                    },
                })
            );
        } else {
            this.abHilitePattern = undefined;
            this.store.clearFilter(false);
        }
    },

    delayUtil: new Ext.util.DelayedTask(),

    /*******************************************************************
     *
     * Private hiliteSearch
     *
     ******************************************************************/

    hiliteSearch: function (_dataIndex, value) {
        let result = value.toString();

        if (this.abHilitePattern !== undefined) {
            result = result.replace(this.abHilitePattern, (_str, g1) => '<span class="txt-inverted-text">' + g1 + '</span>');
        }

        return result;
    },

    /*******************************************************************
     *
     * Private prettyBytes
     *
     ******************************************************************/

    prettyBytes: function (_dataIndex, value) {
        return Josa.Utilities.prettyBytes(value, false, false);
    },

    /******************************************************************
     *
     *  initComponent
     *
     ******************************************************************/

    initComponent: function () {
        //  Add our top toolbar

        this.tbar = [
            'Search',
            {
                xtype: 'triggerfield',
                name: 'searchField',
                width: 260,

                maxLength: 32,
                enforceMaxLength: true,

                hideLabel: true,
                enableKeyEvents: true,
                fieldStyle: { textTransform: 'lowercase' },
                triggerBaseCls: 'x-form-trigger',
                triggerCls: 'x-form-clear-trigger',

                onTriggerClick: function () {
                    this.reset();
                },

                listeners: {
                    change: {
                        fn: this.onTextFieldChange,
                        buffer: 100,
                    },

                    specialkey: function (field, e) {
                        // e.HOME, e.END, e.PAGE_UP, e.PAGE_DOWN,
                        // e.TAB, e.ESC, arrow keys: e.LEFT, e.RIGHT, e.UP, e.DOWN

                        if (e.getKey() === e.ENTER) {
                            this.delayUtil.delay(0, this.delaytask, this, [
                                {
                                    store: this.getStore(),
                                    value: field.getValue(),
                                },
                            ]);
                        }
                    },

                    scope: this,
                },
            },
        ];

        this.store = Ext.create('Josa.ab.store', {});
        this.columns = this.buildColumns();
        this.callParent();
    },

    /*******************************************************************
     *
     *   Private buildColumns
     *
     ******************************************************************/

    /* eslint no-unused-vars: ["error", { "argsIgnorePattern": "col|row|metadata|record|view|store" }] */
    /* eslint no-param-reassign: ["error", { "props": true, "ignorePropertyModificationsFor": ["m"] }]*/

    buildColumns: function () {
        return {
            defaults: {
                sortable: true,
                editor: {
                    xtype: 'textfield',
                    allowBlank: false,
                    selectOnFocus: true,
                },
            },

            items: [
                {
                    header: 'A',
                    xtype: 'actioncolumn',
                    dataIndex: 'rar_albumart',
                    width: 24,
                    hideable: false,
                    sortable: false,
                    groupable: false,
                    getClass: function (value /*, metadata, record*/) {
                        if (value === true) {
                            return 'icon-grid-checked';
                        }
                        return 'icon-grid-warning-red';
                    },
                },

                {
                    header: 'S',
                    xtype: 'actioncolumn',
                    dataIndex: 'rar_albumart_size',
                    width: 24,
                    hideable: false,
                    sortable: false,
                    groupable: false,

                    getClass: function (value, _metadata, _record) {
                        if (value === null) {
                            return 'icon-grid-warning-red';
                        }

                        const dim = value.split(' ');
                        const width = parseInt(dim[0], 10);
                        const height = parseInt(dim[2], 10);

                        if (width < 300 || height < 300 || height > 550 || height > 550) {
                            return 'icon-grid-warning-red';
                        }

                        return 'icon-grid-checked';
                    },
                },

                {
                    header: 'R',
                    xtype: 'actioncolumn',
                    dataIndex: 'rar_albumart_size',
                    width: 24,
                    hideable: false,
                    sortable: false,
                    groupable: false,

                    getClass: function (value, _metadata, _record) {
                        if (value === null) {
                            return 'icon-grid-warning-red';
                        }

                        const dim = value.split(' ');
                        const width = parseInt(dim[0], 10);
                        const height = parseInt(dim[2], 10);

                        if (Math.abs(width - height) > 10) {
                            return 'icon-grid-warning-red';
                        }

                        return 'icon-grid-checked';
                    },
                },

                {
                    header: 'O',
                    dataIndex: 'rar_other_files',
                    width: 32,
                    align: 'right',
                    renderer: function (value, m, record, _row, _col, _store, _view) {
                        if (value !== 0) {
                            const qtip = record.get('rar_other_list').join('<br>');

                            m.tdCls = 'txt-warning-text';
                            m.tdAttr = "data-qtip='" + qtip + "'";
                            return value;
                        }
                        return '';
                    },
                },

                {
                    header: 'Author',
                    dataIndex: 'mp3_author',
                    flex: 1,
                    renderer: function (value, m, record, _row, col, _store, _view) {
                        let art = record.get('rar_albumart_name');

                        if (!Ext.isEmpty(art)) {
                            art = art.replace("'", '&apos;');
                            // eslint-disable-next-line operator-linebreak
                            m.tdAttr =
                                "data-qtip='" +
                                '<span class="album-art-dim">' +
                                'Dimensions: ' +
                                record.get('rar_albumart_size') +
                                '</span><br><img src="' +
                                'audiobooks/images/' +
                                art +
                                '">' +
                                "'";
                        }

                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },

                {
                    header: 'Album',
                    dataIndex: 'mp3_album',
                    flex: 2,
                    renderer: function (value, m, record, _row, col, _store, _view) {
                        let art = record.get('rar_albumart_name');

                        if (!Ext.isEmpty(art)) {
                            art = art.replace("'", '&apos;');
                            m.tdAttr =
                                "data-qtip='" +
                                '<span class="album-art-dim">' +
                                'Dimensions: ' +
                                record.get('rar_albumart_size') +
                                '</span><br><img width="250" height="250" src="' +
                                'audiobooks/images/' +
                                art +
                                '">' +
                                "'";
                        }

                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },
                {
                    header: 'Album (mp3)',
                    dataIndex: 'rar_mp3_album',
                    flex: 2,
                },
                {
                    header: 'Year',
                    dataIndex: 'mp3_year',
                    align: 'right',
                    width: 60,
                    renderer: function (value, _m, _record, _row, col, _store, _view) {
                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },

                {
                    header: 'Narrator',
                    dataIndex: 'mp3_narrator',
                    flex: 1,
                    renderer: function (value, m, record, _row, col, _store, _view) {
                        if (record.get('rar_mp3_artist') !== record.get('mp3_narrator')) {
                            m.tdCls = 'txt-warning-text';
                        }

                        m.tdAttr = "data-qtip='" + value + "'";

                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },

                {
                    header: 'Artist (mp3)',
                    dataIndex: 'rar_mp3_artist',
                    flex: 1,
                    renderer: function (value, m, record, _row, col, _store, _view) {
                        if (record.get('rar_mp3_artist') !== record.get('mp3_narrator')) {
                            m.tdCls = 'txt-warning-text';
                        }

                        m.tdAttr = "data-qtip='" + value + "'";

                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },

                {
                    header: 'Genre (mp3)',
                    dataIndex: 'rar_mp3_genre',
                    width: 80,
                    renderer: function (value, m, _record, _row, col, _store, _view) {
                        if (value !== 'Audiobook') {
                            m.tdCls = 'txt-warning-text';
                        }
                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },

                {
                    header: 'Duration (mp3)',
                    dataIndex: 'rar_mp3_duration',
                    width: 80,
                    align: 'right',
                    renderer: function (value, _m, _record, _row, col, _store, _view) {
                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },

                {
                    header: 'Timestamp',
                    dataIndex: 'file_timestamp',
                    width: 120,
                    renderer: function (value, _m, _record, _row, col, _store, _view) {
                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },

                {
                    header: 'Size',
                    dataIndex: 'file_size',
                    align: 'right',
                    width: 80,
                    renderer: function (value, m, _record, _row, col, _store, _view) {
                        m.tdAttr = "data-qtip='" + value + " Byte(s)'";
                        return this.prettyBytes(this.columns[col].dataIndex, value);
                    },
                },
                {
                    header: 'Art (rar)',
                    dataIndex: 'rar_albumart_size',
                    align: 'right',
                    width: 80,
                    renderer: function (value, _m, _record, _row, col, _store, _view) {
                        if (value == null) {
                            return 'n/a';
                        }
                        return this.hiliteSearch(this.columns[col].dataIndex, value);
                    },
                },
            ],
        };
    },
});
