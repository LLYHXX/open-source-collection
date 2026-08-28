import { Stack, Typography } from "@mui/material";
import React, { useState } from "react";
import { EvalsButton } from "./StyleComponents";
import SvgColor from "../../../components/svg-color";
import PropTypes from "prop-types";
import DuplicateEvals from "./DuplicateEvals";
import { useEvaluationContext } from "./context/EvaluationContext";
import { ShowComponent } from "src/components/show/ShowComponent";
import ConfirmDialog from "src/components/custom-dialog/confirm-dialog";
import { enqueueSnackbar } from "notistack";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Events, PropertyName, trackEvent } from "src/utils/Mixpanel";
import axios, { endpoints } from "src/utils/axios";
import { LoadingButton } from "@mui/lab";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";
import { useAuthContext } from "src/auth/hooks";

const EvalsActions = ({ evalItem, eval_category, tags }) => {
  const { role } = useAuthContext();
  const { setPlaygroundEvaluation } = useEvaluationContext();
  const [isDelete, setIsDelete] = useState(false);
  const [isDuplicate, setIsDuplicate] = useState(false);
  const queryClient = useQueryClient();

  const onEvaluateClick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    setPlaygroundEvaluation({
      ...evalItem,
      eval_template_tags: [eval_category.toString().toUpperCase(), ...tags],
      evalsActionType: "playground",
    });
    trackEvent(Events.evalsPlaygroundClicked, {
      [PropertyName.evalId]: evalItem?.id,
      [PropertyName.evalType]: eval_category,
    });
  };

  const onEditClick = (e) => {
    e.stopPropagation();
    setPlaygroundEvaluation({
      ...evalItem,
      eval_template_tags: [eval_category.toString().toUpperCase(), ...tags],
      evalsActionType: "edit",
    });
    // trackEvent(Events.evalsPlaygroundClicked, {
    //   [PropertyName.evalId]: evalItem?.id,
    //   [PropertyName.evalType]: eval_category,
    // });
  };

  const onDuplicateClick = (e) => {
    e.stopPropagation();
    setIsDuplicate(true);
    // trackEvent(Events.evalsPlaygroundClicked, {
    //   [PropertyName.evalId]: evalItem?.id,
    //   [PropertyName.evalType]: eval_category,
    // });
  };

  const onDeleteClick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    setIsDelete(true);
    // trackEvent(Events.evalsPlaygroundClicked, {
    //   [PropertyName.evalId]: evalItem?.id,
    //   [PropertyName.evalType]: eval_category,
    // });
  };

  const { mutate: handleDelete, isPending } = useMutation({
    mutationFn: () =>
      axios.post(endpoints.develop.eval.deleteEvalsTemplate, {
        eval_template_id: evalItem?.id,
      }),
    onSuccess: () => {
      enqueueSnackbar(`${evalItem?.name} evaluation has been deleted`, {
        variant: "success",
      });
      setIsDelete(false);
      queryClient.invalidateQueries({
        queryKey: ["develop", "user-eval-list"],
      });
    },
  });

  return (
    <>
      <Stack direction="row" spacing={1}>
        <EvalsButton
          size="small"
          onClick={onEvaluateClick}
          startIcon={
            <SvgColor
              sx={{
                width: "16px",
                height: "16px",
                color: "text.disabled",
              }}
              src="/assets/icons/navbar/ic_get_started.svg"
            />
          }
        >
          Playground
        </EvalsButton>
        <ShowComponent
          condition={
            eval_category === "user_built" &&
            RolePermission.EVALS[PERMISSIONS.EDIT_CREATE_DELETE_EVALS][role]
          }
        >
          <EvalsButton
            size="small"
            onClick={onEditClick}
            sx={{
              minWidth: "32px",
              maxWidth: "32px",
              "& .MuiButton-startIcon": { marginLeft: 0, marginRight: 0 },
            }}
            startIcon={
              <SvgColor
                sx={{ width: "16px", height: "16px" }}
                src="/assets/icons/ic_edit_pencil.svg"
              />
            }
          />
          <EvalsButton
            size="small"
            onClick={onDuplicateClick}
            sx={{
              minWidth: "32px",
              maxWidth: "32px",
              "& .MuiButton-startIcon": { marginLeft: 0, marginRight: 0 },
            }}
            startIcon={
              <SvgColor
                sx={{ width: "16px", height: "16px" }}
                src="/assets/icons/custom/duplicate.svg"
              />
            }
          />
          <EvalsButton
            size="small"
            onClick={onDeleteClick}
            sx={{
              minWidth: "32px",
              maxWidth: "32px",
              "& .MuiButton-startIcon": { marginLeft: 0, marginRight: 0 },
            }}
            startIcon={
              <SvgColor
                sx={{ width: "16px", height: "16px" }}
                src="/assets/icons/custom/delete.svg"
              />
            }
          />
        </ShowComponent>
      </Stack>
      <ConfirmDialog
        onClick={(e) => e.stopPropagation()}
        open={isDelete}
        maxWidth="xs"
        onClose={() => setIsDelete(false)}
        title={"Delete Evaluation"}
        content={
          <Typography
            typography={"s1"}
            fontWeight={"fontWeightRegular"}
            color="text.primary"
          >
            Are you sure you’d like to delete this evaluation :
            <b> {evalItem?.name || "Unnamed Evaluation"}</b> Once deleted, the
            evaluation applied on the platform will also be deleted.
          </Typography>
        }
        action={
          <LoadingButton
            onClick={handleDelete}
            variant="contained"
            size="small"
            color="error"
            loading={isPending}
          >
            Delete Evaluation
          </LoadingButton>
        }
      />
      <DuplicateEvals
        open={isDuplicate}
        onClose={() => setIsDuplicate(false)}
        evalId={evalItem?.id}
        onSubmit={(data) => {
          if (data?.eval_template_id) {
            queryClient.invalidateQueries({
              queryKey: ["develop", "user-eval-list"],
            });
            setPlaygroundEvaluation({
              ...evalItem,
              id: data?.eval_template_id,
              eval_template_tags: [
                eval_category.toString().toUpperCase(),
                ...tags,
              ],
              evalsActionType: "edit",
            });
          }
        }}
      />
    </>
  );
};

export default EvalsActions;

EvalsActions.propTypes = {
  evalItem: PropTypes.object,
  eval_category: PropTypes.string,
  tags: PropTypes.array,
};
