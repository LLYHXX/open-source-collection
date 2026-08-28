import PropTypes from "prop-types";
import NewAnnotationCellRenderer from "../../../sections/agents/NewAnnotationCellRenderer";

const AnnotationValueCellRenderer = (props) => {
  const annotationType = props?.data?.type;
  const settings = props?.data?.settings;

  return (
    <NewAnnotationCellRenderer
      value={props?.value}
      annotationType={annotationType}
      settings={settings}
      justifyContent="center"
    />
  );
};

AnnotationValueCellRenderer.propTypes = {
  value: PropTypes.string,
  column: PropTypes.object,
  data: PropTypes.object,
};

export default AnnotationValueCellRenderer;
