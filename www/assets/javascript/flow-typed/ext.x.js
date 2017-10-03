// @flow
declare class Ext {
    static onReady(fn: Function): void,

    static apply(object: any, config: any, defaults?: any): any,
    static create(name: string, ...args: any[]): any,
    static define(className: string, data: any, createdFn?: Function): void,
    static isEmpty(value?: any, allowEmptyString?: boolean): boolean,
    static override(target?: any, overrides?: any): void,

    static tip: {
        Tip: {
            prototype: {
                minWidth?: number,
            },
        },
    },

    static getBody(): {
        getViewSize(): {
            width: number,
            height: number,
        },
    },

    static util: {
        DelayedTask(id?: number): void,
        Filter(filterFn?: any): void,
    },

    static Object: {
        each(iterable?: any, fn?: any, scope?: any, reverse?: boolean): boolean,
    },

    static QuickTips: {
        init(): void,
        getQuickTip(): void,
    },
}

declare module 'Ext' {
    declare module.exports: Class<Ext>;
}
