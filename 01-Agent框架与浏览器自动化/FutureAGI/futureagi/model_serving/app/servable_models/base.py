from abc import ABC, abstractmethod


class ModelServing(ABC):
    @abstractmethod
    def __init__(self):
        """
        Initialize the model serving instance. This method should be overridden
        by child classes to set up model-specific configurations or parameters.
        """
        pass

    @abstractmethod
    def preprocess(self, data):
        """
        Preprocess the input data before feeding it to the model.

        Args:
            data: The raw input data that needs to be preprocessed.

        Returns:
            Processed data ready for the model.

        This method should be overridden by child classes to implement
        model-specific preprocessing steps.
        """
        pass

    @abstractmethod
    def forward(self, data):
        """
        Perform a forward pass through the model using the preprocessed data.

        Args:
            data: The preprocessed data that will be passed through the model.

        Returns:
            The model's output based on the input data.

        This method should be overridden by child classes to implement
        the model's inference logic.
        """
        pass

    @abstractmethod
    def postprocess(self, output):
        """
        Postprocess the model's output to make it suitable for return or further
        use.

        Args:
            output: The raw output from the model that needs to be postprocessed.

        Returns:
            The final output after applying postprocessing steps.

        This method should be overridden by child classes to implement
        model-specific postprocessing steps.
        """
        pass
