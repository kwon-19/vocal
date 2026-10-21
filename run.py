
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from pybo import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
