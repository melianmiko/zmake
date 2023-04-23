const __App__ = (config) => {
    __$$hmAppManager$$__.currentApp.app = DeviceRuntimeCore.App(config);
};
const __Page__ = (config) => {
    __$$hmAppManager$$__.currentApp.current.module = DeviceRuntimeCore.Page(config);
};
const __WatchFace__ = (config) => {
    __$$hmAppManager$$__.currentApp.current.module = DeviceRuntimeCore.WatchFace(config);
};
const __getApp = () => {
    return __$$hmAppManager$$__.currentApp.app;
};
const __px__ = (v) => v;

export {
    __App__ as "App",
    __Page__ as "Page",
    __WatchFace__ as "WatchFace",
    __getApp as "getApp",
    __px__ as "px"
};
