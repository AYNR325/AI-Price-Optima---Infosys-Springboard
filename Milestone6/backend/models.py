# import joblib
# import pandas as pd
# import numpy as np
# import os

# class PricingModel:
#     def __init__(self, model_path='pricing_model_artifacts.pkl'):
#         self.artifacts = None
#         self.model = None
#         self.le_location = None
#         self.le_time = None
#         self.loyalty_mapping = None
#         self.vehicle_mapping = None
#         self.feature_cols = None
#         self.load(model_path)

#     def load(self, model_path):
#         if os.path.exists(model_path):
#             print(f"Loading model artifacts from {model_path}")
#             self.artifacts = joblib.load(model_path)
#             self.model = self.artifacts['model']
#             self.le_location = self.artifacts['le_location']
#             self.le_time = self.artifacts['le_time']
#             self.loyalty_mapping = self.artifacts['loyalty_mapping']
#             self.vehicle_mapping = self.artifacts['vehicle_mapping']
#             self.feature_cols = self.artifacts['feature_cols']
#         else:
#             print(f"Model artifacts not found at {model_path}")

#     def predict(self, input_data):
#         if not self.model:
#             raise Exception("Model not loaded")
        
#         df = pd.DataFrame(input_data)
        
#         df['Demand_Ratio'] = df['Number_of_Riders'] / (df['Number_of_Drivers'] + 1e-5)
#         df['Supply_Constraint'] = (df['Number_of_Riders'] > df['Number_of_Drivers']).astype(int)
#         df['Market_Saturation'] = df['Number_of_Drivers'] / (df['Number_of_Riders'] + 1e-5)
#         df['Rider_Loyalty_Score'] = df['Number_of_Past_Rides'] * 0.5 + df['Average_Ratings'] * 10
#         df['Duration_Per_Rider'] = df['Expected_Ride_Duration'] / (df['Number_of_Riders'] + 1e-5)
#         df['Capacity_Utilization'] = df['Demand_Ratio'] / (df['Demand_Ratio'].max() + 1e-5)
        
#         premium_vehicle = df['Vehicle_Type'].map(self.vehicle_mapping)
#         df['Premium_Factor'] = premium_vehicle * df['Average_Ratings']
#         df['Surge_Indicator'] = 0 
        
#         df['Location_Encoded'] = self.le_location.transform(df['Location_Category'])
#         df['Time_Encoded'] = self.le_time.transform(df['Time_of_Booking'])
#         df['Loyalty_Encoded'] = df['Customer_Loyalty_Status'].map(self.loyalty_mapping)
#         df['Vehicle_Encoded'] = df['Vehicle_Type'].map(self.vehicle_mapping)
        
#         X = df[self.feature_cols]
#         prediction = self.model.predict(X)
#         return prediction.tolist()

# pricing_model = PricingModel()


import joblib
import pandas as pd
import numpy as np
import os

class PricingModel:
    def __init__(self, model_path=None):
        # Set absolute path to model file inside Docker
        if model_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(base_dir, "pricing_model_artifacts.pkl")

        print("Looking for model at:", model_path)
        self.artifacts = None
        self.model = None
        self.le_location = None
        self.le_time = None
        self.loyalty_mapping = None
        self.vehicle_mapping = None
        self.feature_cols = None
        self.load(model_path)

    def load(self, model_path):
        if os.path.exists(model_path):
            print(f"Loading model artifacts from {model_path}")
            self.artifacts = joblib.load(model_path)
            self.model = self.artifacts['model']
            self.le_location = self.artifacts['le_location']
            self.le_time = self.artifacts['le_time']
            self.loyalty_mapping = self.artifacts['loyalty_mapping']
            self.vehicle_mapping = self.artifacts['vehicle_mapping']
            self.feature_cols = self.artifacts['feature_cols']
        else:
            print(f"❌ Model artifacts not found at {model_path}")

    def predict(self, input_data):
        if not self.model:
            raise Exception("Model not loaded")

        df = pd.DataFrame(input_data)

        df['Demand_Ratio'] = df['Number_of_Riders'] / (df['Number_of_Drivers'] + 1e-5)
        df['Supply_Constraint'] = (df['Number_of_Riders'] > df['Number_of_Drivers']).astype(int)
        df['Market_Saturation'] = df['Number_of_Drivers'] / (df['Number_of_Riders'] + 1e-5)
        df['Rider_Loyalty_Score'] = df['Number_of_Past_Rides'] * 0.5 + df['Average_Ratings'] * 10
        df['Duration_Per_Rider'] = df['Expected_Ride_Duration'] / (df['Number_of_Riders'] + 1e-5)
        df['Capacity_Utilization'] = df['Demand_Ratio'] / (17.6 + 1e-5) # Fixed max from training data
        
        premium_vehicle = df['Vehicle_Type'].map(self.vehicle_mapping)
        df['Premium_Factor'] = premium_vehicle * df['Average_Ratings']
        
        # Fixed threshold from training data (3.8)
        df['Surge_Indicator'] = (df['Demand_Ratio'] > 3.8).astype(int)

        df['Location_Encoded'] = self.le_location.transform(df['Location_Category'])
        df['Time_Encoded'] = self.le_time.transform(df['Time_of_Booking'])
        df['Loyalty_Encoded'] = df['Customer_Loyalty_Status'].map(self.loyalty_mapping)
        df['Vehicle_Encoded'] = df['Vehicle_Type'].map(self.vehicle_mapping)

        X = df[self.feature_cols]
        base_prediction = self.model.predict(X)
        
        # Apply Logic Rules
        final_prediction = []
        for i, price in enumerate(base_prediction):
            adjusted_price = self.apply_dynamic_pricing_rules(price, df.iloc[i])
            final_prediction.append(adjusted_price)
            
        return final_prediction

    def apply_dynamic_pricing_rules(self, base_price, row):
        """
        Manually adjust price based on strong market signals 
        that might be diluted in the ML model.
        """
        adjusted_price = base_price
        
        # 1. Discount Rules (Low Demand / High Supply)
        if row['Demand_Ratio'] < 0.3:
            # Low demand -> 20% Discount
            adjusted_price = adjusted_price * 0.80
            
        if row['Market_Saturation'] > 2.0:
            # Too many drivers -> Additional 15% Discount
            adjusted_price = adjusted_price * 0.85
            
        # 2. Surge Rules (High Demand)
        # Relaxed threshold: Check if demand is just 20% higher than supply
        if row['Demand_Ratio'] > 1.2:
             # Progressive Surge
            multiplier = 1.2
            if row['Demand_Ratio'] > 2.0:
                multiplier = 1.5 
            if row['Surge_Indicator'] == 1:
                multiplier += 0.1
            adjusted_price = adjusted_price * multiplier
            
        # 3. Premium Vehicle Logic (Enforce Higher Price)
        if row['Vehicle_Type'] == 'Premium':
            adjusted_price = adjusted_price * 1.25

        # 4. Hard Floor
        final_price = max(50.0, adjusted_price)
        
        # 5. Global Normalizer (Model predictions are naturally high)
        return final_price * 0.55


pricing_model = PricingModel()
