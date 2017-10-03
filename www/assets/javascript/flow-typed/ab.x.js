// @flow

declare class Josa {
    static Utilities: {
        prettyBytes(a: number, b: boolean, c: boolean): string,
    },
    static ab: {
        storemodel: string,
    },
}

declare class abConfig {
    static settings: {
        winMargin: number,
        urls: {
            ab?: string,
        },
    },
}
