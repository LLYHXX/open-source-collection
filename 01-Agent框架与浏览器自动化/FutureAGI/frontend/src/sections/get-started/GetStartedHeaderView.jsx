import Box from "@mui/material/Box/Box";
import Link from "@mui/material/Link";
import PropTypes from "prop-types";
import React from "react";
import PageHeadings from "../develop-detail/Common/PageHeadings";
import { handleOnDocsClicked } from "src/utils/Mixpanel";

const GetStartedHeaderView = ({ setShowDemoModal: _setShowDemoModal }) => {
  return (
    <Box
      display={"flex"}
      flexDirection={"row"}
      // alignItems={"center"}
      width={"100%"}
      justifyContent={"space-between"}
      alignItems={"center"}
    >
      <Box>
        <PageHeadings
          title="Get Started with FutureAGI"
          description={
            <>
              {`This tour will guide you through the key features and functionalities `}
              <Link
                href="https://docs.futureagi.com"
                target="_blank"
                underline="always"
                variant="s1"
                fontWeight={"fontWeightSemiBold"}
                color="primary.light"
                onClick={() => handleOnDocsClicked("get_started_page")}
              >
                View docs
              </Link>
            </>
          }
        />
      </Box>
      {/* <Button
        variant="outlined"
        color="primary"
        size="small"
        sx={
          {
            // height: "38px",
            // px: "24px",
            // py: "8px",
          }
        }
        startIcon={
          <SvgColor
            src={`/assets/icons/action_buttons/ic_play.svg`}
            sx={{
              width: 16,
              height: 16,
              color: "primary.main",
            }}
          />
        }
        onClick={handleClick}
      >
        Watch demo
      </Button> */}
    </Box>
  );
};

export default GetStartedHeaderView;

GetStartedHeaderView.propTypes = {
  setShowDemoModal: PropTypes.func,
};
