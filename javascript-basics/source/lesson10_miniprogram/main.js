{
  let pageConfig = null;
  global.Page = (config) => {
    pageConfig = config;
  };

  Page({
    data: { count: 0, title: "计数器" },
    onLoad() {
      console.log("页面加载：", this.data.title);
    },
    onTap() {
      this.setData({ count: this.data.count + 1 });
      console.log("点击后 count =", this.data.count);
    }
  });

  function createPage(config) {
    const instance = {
      data: { ...config.data },
      setData(patch) {
        this.data = { ...this.data, ...patch };
        config.data = this.data;
      }
    };
    for (const key of Object.keys(config)) {
      if (typeof config[key] === "function") {
        instance[key] = config[key];
      }
    }
    return instance;
  }

  const page = createPage(pageConfig);
  page.onLoad();
  page.onTap();
  page.onTap();
}


{
  let pageConfig = null;
  global.Page = (config) => {
    pageConfig = config;
  };

  Page({
    data: {
      items: [
        { id: 1, title: "JavaScript" },
        { id: 2, title: "Node" }
      ],
      selected: ""
    },
    onItemTap(event) {
      const id = event.currentTarget.dataset.id;
      const item = this.data.items.find((row) => row.id === id);
      this.setData({ selected: item.title });
      console.log("选中：", this.data.selected);
    }
  });

  const instance = {
    data: { ...pageConfig.data },
    setData(patch) {
      this.data = { ...this.data, ...patch };
    },
    onItemTap: pageConfig.onItemTap
  };

  instance.onItemTap({ currentTarget: { dataset: { id: 2 } } });
}


{
  const event = {
    type: "tap",
    currentTarget: { dataset: { id: 2 } },
    detail: { x: 10, y: 20 }
  };

  console.log("事件类型：", event.type);
  console.log("带出的 id：", event.currentTarget.dataset.id);
  console.log("坐标：", event.detail.x, event.detail.y);
}
