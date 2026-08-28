import React from "react";
import ComplexFilter from "./ComplexFilter";
import logger from "src/utils/logger";

const meta = {
  component: ComplexFilter,
  title: "Components/ComplexFilter",
  parameters: {
    docs: {
      description: {
        component: "ComplexFilter",
      },
    },
  },
};
export default meta;

const Template = (args) => {
  return <ComplexFilter {...args} />;
};

const defaultFilter = {
  id: "1",
  name: "",
  email: "",
  date: "",
  status: "",
  dependentName: "",
  dependentEmail: "",
  dependentDate: "",
  dependentStatus: "",
  number: "",
  dependentNumber: "",
};

const setFilters = (newFilters) => {
  logger.debug(newFilters);
};

export const TextFilter = Template.bind({});

TextFilter.args = {
  filters: [defaultFilter],
  defaultFilter: defaultFilter,
  setFilters: setFilters,
  filterDefinition: [
    {
      propertyName: "Name",
      propertyId: "name",
      filterType: "text",
      dependents: [
        {
          stringConnector: "is",
          propertyName: "Dependent Name",
          propertyId: "dependentName",
          filterType: "text",
        },
      ],
    },
    {
      propertyName: "Email",
      propertyId: "email",
      filterType: "text",
      dependents: [
        {
          stringConnector: "is",
          propertyName: "Dependent Email",
          propertyId: "dependentEmail",
          filterType: "text",
        },
      ],
    },
  ],
};

export const DateFilter = Template.bind({});

DateFilter.args = {
  filters: [defaultFilter],
  defaultFilter: defaultFilter,
  setFilters: setFilters,
  filterDefinition: [
    {
      propertyName: "Date",
      propertyId: "date",
      filterType: "date",
      dependents: [
        {
          stringConnector: "is",
          propertyName: "Dependent Date",
          propertyId: "dependentDate",
          filterType: "date",
        },
      ],
    },
  ],
};

export const OptionsFilter = Template.bind({});

OptionsFilter.args = {
  filters: [defaultFilter],
  defaultFilter: defaultFilter,
  setFilters: setFilters,
  filterDefinition: [
    {
      propertyName: "Status",
      propertyId: "status",
      filterType: "options",
      options: [
        { value: "active", label: "Active" },
        { value: "inactive", label: "Inactive" },
      ],
      dependents: [
        {
          stringConnector: "is",
          propertyName: "Dependent Status",
          propertyId: "dependentStatus",
          filterType: "options",
          options: [
            { value: "active", label: "Active" },
            { value: "inactive", label: "Inactive" },
          ],
        },
      ],
    },
  ],
};

export const NumberFilter = Template.bind({});

NumberFilter.args = {
  filters: [defaultFilter],
  defaultFilter: defaultFilter,
  setFilters: setFilters,
  filterDefinition: [
    {
      propertyName: "Number",
      propertyId: "number",
      filterType: "number",
      dependents: [
        {
          stringConnector: "is",
          propertyName: "Dependent Number",
          propertyId: "dependentNumber",
          filterType: "number",
        },
      ],
    },
  ],
};
