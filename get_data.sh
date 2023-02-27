conda activate allcause
python download_1969.py
python -c "from allcause.data import get_all_mortality_data; _= get_all_mortality_data()"