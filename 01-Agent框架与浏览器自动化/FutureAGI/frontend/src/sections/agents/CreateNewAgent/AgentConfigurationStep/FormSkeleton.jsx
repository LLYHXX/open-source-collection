import { Box, Skeleton } from "@mui/material";

export default function FormSkeleton() {
  return (
    <Box sx={{ width: "100%" }}>
      {/* Voice/Chat Provider */}
      <Box sx={{ mb: 3 }}>
        <Skeleton variant="text" width={150} height={20} sx={{ mb: 1 }} />
        <Skeleton variant="rounded" width="100%" height={56} />
      </Box>

      {/* Authentication Method */}
      <Box sx={{ mb: 3 }}>
        <Skeleton variant="text" width={180} height={20} sx={{ mb: 1 }} />
        <Skeleton variant="rounded" width="100%" height={56} />
      </Box>

      {/* Provider API Key */}
      <Box sx={{ mb: 3 }}>
        <Skeleton variant="text" width={140} height={20} sx={{ mb: 1 }} />
        <Skeleton variant="rounded" width="100%" height={56} />
      </Box>

      {/* Assistant ID */}
      <Box sx={{ mb: 3 }}>
        <Skeleton variant="text" width={100} height={20} sx={{ mb: 1 }} />
        <Skeleton variant="rounded" width="100%" height={56} />
      </Box>
    </Box>
  );
}
