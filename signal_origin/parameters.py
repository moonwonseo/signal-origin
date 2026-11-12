"""JSON parameter export and independent probability reconstruction from V1."""
import numpy as np
from scipy.special import expit

def export_model(model,feature_order):
    sc=model.named_steps['scale'];lr=model.named_steps['logit']
    return {'features':list(feature_order),'scaler_mean':sc.mean_.tolist(),'scaler_scale':sc.scale_.tolist(),'coefficients_standardized':lr.coef_[0].tolist(),'intercept':float(lr.intercept_[0]),'iterations':int(lr.n_iter_[0]),'classes':lr.classes_.tolist(),'n_training_rows':int(sc.n_samples_seen_),'interpretation':'Association only; coefficients are not causal estimates.'}

def probabilities_from_json(frame,params):
    x=frame.loc[:,params['features']].to_numpy(dtype=float)
    return expit(((x-np.array(params['scaler_mean']))/np.array(params['scaler_scale']))@np.array(params['coefficients_standardized'])+params['intercept'])
