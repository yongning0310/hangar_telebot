import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from data.data import load_data, save_data
from webappbot import add_new_dates

@patch('webappbot.load_data')
@patch('webappbot.save_data')
def test_add_new_dates(mock_save_data, mock_load_data):
    # Mock the data returned by load_data
    mock_load_data.return_value = {
        'dates': {},
        'seats': {'1': {'is_broken': False}}
    }

    # Call the function
    add_new_dates()

    # Check that save_data was called with the expected data
    expected_data = {
        'dates': {
            (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'): {
                datetime.strptime(str(hour), "%H").strftime("%H:%M"): {'1': {'is_booked': False}}
                for hour in range(0, 24)
            } for i in range(7)
        },
        'seats': {'1': {'is_broken': False}}
    }
    mock_save_data.assert_called_once_with(expected_data)