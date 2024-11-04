import numpy as np
import pandas as pd

class Sample:
    """
    A class designed to encapsulate the data for a single sample and
    all associated functionality and metadata.

    Attributes
    ----------
    _name : str
        The name of the sample.
    _scaling_type : str
        The scaling type for the sample. This can be either 'pot' or
        'livetime'.
    _file_handle : uproot.reading.ReadOnlyDirectory
        The file handle for the input ROOT file.
    _exposure_pot : float
        The exposure of the sample in POT.
    _exposure_livetime : float
        The exposure of the sample in livetime.
    _data : pd.DataFrame
        The data comprising the sample.
    """
    def __init__(self, name, rf, key, scaling_type, override_category=None) -> None:
        """
        Initializes the Sample object with the given name and key.

        Parameters
        ----------
        name : str
            The name of the sample.
        rf : uproot.reading.ReadOnlyDirectory
            The file handle for the input ROOT file.
        key : str
            The key/name of the TDirectory in the ROOT file input
            containing the sample data.
        scaling_type : str
            The scaling type for the sample. This can be either 'pot'
            or 'livetime'. This is used for matching the exposure of
            the sample to the target sample.

        Returns
        -------
        None.
        """
        self._name = name
        self._scaling_type = scaling_type
        self._file_handle = rf[f'events/{key}']
        self._exposure_pot = self._file_handle['POT'].to_numpy()[0][0]
        self._exposure_livetime = self._file_handle['Livetime'].to_numpy()[0][0]

        # TODO: Make this follow a setting in the config.
        self._data = self._file_handle['selectedNu'].arrays(library='pd')
        if override_category is not None:
            # TODO: Make this follow the category_tree setting in the config.
            self._data['category'] = override_category

    def override_exposure(self, exposure, exposure_type='pot') -> None:
        """
        Overrides the exposure for the sample. This is useful for
        setting the exposure for samples for which the exposure is not
        valid. The exposure type can be either 'pot' or 'livetime'. It
        is not recommended to use this method unless the exposure is
        known to be incorrect.

        Parameters
        ----------
        exposure : float
            The exposure to set for the sample.
        exposure_type : str
            The type of exposure to set. This can be either 'pot' or
            'livetime'. The default is 'pot'.

        Returns
        -------
        None.
        """
        if exposure_type == 'pot':
            self._exposure_pot = exposure
        else:
            self._exposure_livetime = exposure

    def set_weight(self, target=None) -> None:
        """
        Sets the weight for the sample to the target value.

        Parameters
        ----------
        target : Sample
            The Sample object to use as the exposure normalization
            target. This is used to scale the weight of this sample to
            the target sample. If None, the weight is set to 1.
        
        Returns
        -------
        None.
        """
        if target is None:
            self._data['weight'] = 1
        elif self._scaling_type == 'pot':
            self._data['weight'] = (target._exposure_pot / self._exposure_pot)
            print(f"Setting weight for {self._name} to {target._exposure_pot / self._exposure_pot}")
        else:
            self._data['weight'] = (target._exposure_livetime / self._exposure_livetime)
            print(f"Setting weight for {self._name} to {target._exposure_livetime / self._exposure_livetime}")

    def get_data(self, variable) -> dict:
        """
        Returns the data for the given variable in the sample. The data
        is returned as a dictionary with the category as the key and
        the data for the requested variable as the value.

        Parameters
        ----------
        variable : str
            The name of the variable to retrieve.

        Returns
        -------
        data : dict
            The data for the requested variable in the sample. The data
            is stored as a dictionary with the category as the key and
            the data (a pandas Series) as the value.
        weights : dict
            The weights for the requested variable in the sample. The
            weights are stored as a dictionary with the category as the
            key and the weights (a pandas Series) as the value.
        """
        data = {}
        weights = {}
        # TODO: Make this follow the category_tree setting in the config.
        for category in np.unique(self._data['category']):
            data[int(category)] = self._data[self._data['category'] == category][variable]
            weights[int(category)] = self._data[self._data['category'] == category]['weight']
        return data, weights

    def __str__(self) -> str:
        """
        Returns a string representation of the Sample object.
        
        Parameters
        ----------
        None.

        Returns
        -------
        res : str
            A string representation of the Sample object.
        """
        res = f'{"Sample:":<15}{self._name}'
        res += f'\n{"POT:":<15}{self._exposure_pot:.2e}'
        res += f'\n{"Livetime:":<15}{self._exposure_livetime:.2e}'
        return res