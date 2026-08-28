import PropTypes from "prop-types";
import React, { useEffect } from "react";
import "../../../components/annotate/build/static/js/main";

export const LabelStudioComponent = ({ nerData }) => {
  useEffect(() => {
    // new LabelStudio("label-studio-container", {
    //   config: `
    //     <View>
    //       <Text name="text" value="$text"/>
    //       <Labels name="label" toName="text">
    //         <Label value="Person" background="green"/>
    //         <Label value="Organization" background="red"/>
    //         <Label value="Location" background="blue"/>
    //         <Label value="Misc" background="orange"/>
    //       </Labels>
    //     </View>
    //   `,
    //   interfaces: [],
    //   // interfaces: ["panel", "update", "submit"],
    //   task: {
    //     annotations: [],
    //     predictions: [
    //       {
    //         id: 1,
    //         result: annotations,
    //       },
    //     ],
    //     id: 1,
    //     data: {
    //       text: nerData.text,
    //     },
    //   },
    //   onLabelStudioLoad: function (LS) {
    //     if (LS.task && LS.task.predictions && LS.task.predictions.length > 0) {
    //       LS.annotationStore.addAnnotations(LS.task.predictions[0].result);
    //     }
    //   },
    // });
  }, [nerData]);

  return <div id="label-studio-container" />;
};

LabelStudioComponent.propTypes = {
  nerData: PropTypes.object,
};
