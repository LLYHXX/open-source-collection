export function findNearestParentRoute(routes, currentPath) {
  const pathSegments = currentPath.split("/").filter(Boolean);

  for (let i = pathSegments.length - 1; i >= 0; i--) {
    const potentialParentPath = "/" + pathSegments.slice(0, i).join("/");
    const parentRoute = findRouteByPath(routes, potentialParentPath);

    if (parentRoute && parentRoute.isMainRoute) {
      return potentialParentPath;
    }
  }

  return "/dashboard"; // fallback to dashboard if no parent found
}

export function findRouteByPath(routes, path) {
  for (const route of routes) {
    if (route.path === path) {
      return route;
    }
    if (route.children) {
      const childRoute = findRouteByPath(route.children, path);
      if (childRoute) {
        return childRoute;
      }
    }
  }
  return null;
}
