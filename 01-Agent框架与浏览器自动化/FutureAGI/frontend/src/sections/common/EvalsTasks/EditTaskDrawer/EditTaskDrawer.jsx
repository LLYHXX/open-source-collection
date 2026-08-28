import React, { useRef } from "react";
import { ShowComponent } from "src/components/show";
import DetailsEdit from "./DetailsEdit";
import PropTypes from "prop-types";
import { useGetTaskData } from "../common";

const EditTaskDrawer = (props) => {
  const setVisibleSectionRef = useRef(null);
  const handleClose = () => {
    setVisibleSectionRef.current = "list";
    props?.onClose();
  };
  return <EditTaskDrawerChild {...props} onClose={handleClose} />;
};

EditTaskDrawer.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  selectedRow: PropTypes.object,
  refreshGrid: PropTypes.func,
  observeId: PropTypes.string,
  isEdit: PropTypes.bool,
  isView: PropTypes.bool,
};

const EditTaskDrawerChild = ({
  selectedRow,
  refreshGrid,
  onClose,
  isView = false,
  isEdit = false,
  open,
}) => {
  const taskId = selectedRow?.id;

  const { data: taskDetails, isLoading } = useGetTaskData(taskId, {
    enabled: !!taskId,
  });

  return (
    <>
      <ShowComponent condition={!!taskDetails}>
        <DetailsEdit
          loading={isLoading}
          isEdit={isEdit}
          title={selectedRow?.name}
          isView={isView}
          observeId={taskDetails?.project_id}
          taskDetails={taskDetails}
          selectedRow={selectedRow}
          onClose={onClose}
          refreshGrid={refreshGrid}
          open={open}
        />
      </ShowComponent>
    </>
  );
};

EditTaskDrawerChild.propTypes = {
  selectedRow: PropTypes.object,
  refreshGrid: PropTypes.func,
  onClose: PropTypes.func,
  isView: PropTypes.bool,
  isEdit: PropTypes.bool,
  open: PropTypes.bool,
};

export default EditTaskDrawer;
