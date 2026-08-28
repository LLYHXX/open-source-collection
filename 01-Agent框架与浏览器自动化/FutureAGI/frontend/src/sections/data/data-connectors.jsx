import React from "react";
import { Container, Grid, Stack, Typography } from "@mui/material";
import DatasourceWidget from "./datasource-widget";

export default function DataConnectors() {
  return (
    <>
      <Stack
        sx={{
          mt: 2,
        }}
        spacing={2}
      >
        <Container>
          <Typography
            variant="h6"
            sx={{
              mb: { xs: 3, md: 5 },
            }}
          >
            Local Files
          </Typography>
          <Grid container spacing={3}>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
          </Grid>
        </Container>

        <Container>
          <Typography
            variant="h6"
            sx={{
              mb: { xs: 3, md: 5 },
            }}
          >
            SDK
          </Typography>
          <Grid container spacing={3}>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
          </Grid>
        </Container>
        <Container>
          <Typography
            variant="h6"
            sx={{
              mb: { xs: 3, md: 5 },
            }}
          >
            Cloud Storage Import
          </Typography>
          <Grid container spacing={3}>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
          </Grid>
        </Container>
        <Container>
          <Typography
            variant="h6"
            sx={{
              mb: { xs: 3, md: 5 },
            }}
          >
            Cloud Storage
          </Typography>
          <Grid container spacing={3}>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
          </Grid>
        </Container>

        <Container>
          <Typography
            variant="h6"
            sx={{
              mb: { xs: 3, md: 5 },
            }}
          >
            Product Data Import
          </Typography>
          <Grid container spacing={3}>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
            <Grid xs={12} sm={6} md={3}>
              <DatasourceWidget
                title="Weekly Sales"
                total={714000}
                color="warning"
                icon={
                  <img alt="icon" src="/assets/icons/glass/ic_glass_bag.png" />
                }
              />
            </Grid>
          </Grid>
        </Container>
      </Stack>
    </>
  );
}
