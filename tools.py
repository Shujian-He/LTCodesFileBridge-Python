import math
import random

def robust_soliton_distribution(N, c=0.1, delta=0.5):
    """
    Computes the robust Soliton distribution for a block of N symbols using pure Python.
    
    Parameters:
      N     : int   - total number of input symbols.
      c     : float - constant parameter (tuning parameter for robustness).
      delta : float - failure probability.
      
    Returns:
      mu    : list  - a list of length N, where mu[d-1] is the probability
                      for degree d (d = 1, 2, ..., N).
    """
    # Compute the ripple parameter R.
    R = c * math.log(N / delta) * math.sqrt(N)
    
    # Determine the threshold K and ensure it does not exceed N.
    K = int(math.floor(N / R))
    K = min(K, N)  # Adjust K if necessary
    
    # Build the ideal Soliton distribution (rho):
    # rho(1) = 1/N, and for d >= 2, rho(d) = 1/(d*(d-1)).
    rho = [0] * N
    rho[0] = 1.0 / N
    for d in range(2, N + 1):
        rho[d - 1] = 1.0 / (d * (d - 1))
    
    # Build the tau distribution (robustifying part).
    tau = [0] * N
    for d in range(1, K):
        tau[d - 1] = R / (d * N)
    if K <= N:
        tau[K - 1] = R * math.log(R / delta) / N
    
    # Combine the two distributions.
    combined = [r + t for r, t in zip(rho, tau)]
    
    # Normalize so that the probabilities sum to 1.
    total = sum(combined)
    mu = [x / total for x in combined]
    
    return mu

def choose_degree(K):
    pdf = robust_soliton_distribution(K)
    # Create a list of degrees [1, 2, ..., K]
    degrees = list(range(1, K + 1))
    # Use random.choices to select one degree according to the distribution pdf.
    return random.choices(degrees, weights=pdf, k=1)[0]