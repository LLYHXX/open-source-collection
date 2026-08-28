export const getDefaultCreateLabelFormValues = (editData) => {
  let settings = editData?.settings || {};
  if (editData?.type === "categorical" && settings?.options) {
    settings = {
      ...settings,
      options: settings.options.map((opt, idx) => ({
        id: `${idx}-${opt.label}`,
        value: opt.label,
      })),
    };
  }

  return {
    name: editData?.name || "",
    type: editData?.type || "",
    description: editData?.description || "",
    settings,
  };
};

export const AnnotationTypes = [
  { label: "Text", value: "text" },
  { label: "Numeric", value: "numeric" },
  { label: "Categorical", value: "categorical" },
  { label: "Star", value: "star" },
  { label: "Thumbs Up & Down", value: "thumbs_up_down" },
];

export const AnnotationFormDefaultSettings = {
  text: {
    placeholder: "",
    maxLength: "",
    minLength: "",
  },
  numeric: {
    min: "",
    max: "",
    stepSize: "",
    displayType: "",
  },
  categorical: {
    options: [],
    multiChoice: false,
  },
  star: {
    noOfStars: 5,
  },
  thumbs_up_down: {},
};

export const transformLabelObject = (label) => {
  if (label.type === "categorical") {
    return {
      ...label,
      settings: {
        ...label.settings,
        options: label.settings.options.map((option) => ({
          label: option.label,
          value: option.label,
        })),
      },
    };
  }
  return label;
};

export const NumericLabelDisplayTypes = [{ label: "Slider", value: "slider" }];
