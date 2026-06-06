import joblib
import pandas as pd


class CrowdDensityPredictor:

    def __init__(
        self,
        model_path="ml/crowd_density_model.pkl",
        mapping_path="ml/node_mapping.pkl"
    ):
        """
        Load trained model and node mapping.
        """

        self.model = joblib.load(model_path)

        self.node_mapping = joblib.load(
            mapping_path
        )

    # ----------------------------------------
    # Get Encoded Node
    # ----------------------------------------
    def encode_node(self, node_id):

        if node_id in self.node_mapping:
            return self.node_mapping[node_id]

        return -1

    # ----------------------------------------
    # Predict Crowd Density
    # ----------------------------------------
    def predict(
        self,
        node_id,
        hour,
        avg_duration,
        total_bytes
    ):

        node_encoded = (
            self.encode_node(node_id)
        )

        input_df = pd.DataFrame(
            {
                "node_encoded": [
                    node_encoded
                ],
                "hour": [hour],
                "avg_duration": [
                    avg_duration
                ],
                "total_bytes": [
                    total_bytes
                ]
            }
        )

        prediction = (
            self.model.predict(
                input_df
            )[0]
        )

        return round(prediction)

    # ----------------------------------------
    # Batch Prediction
    # ----------------------------------------
    def batch_predict(
        self,
        dataframe
    ):

        return self.model.predict(
            dataframe
        )


# --------------------------------------------
# TEST
# --------------------------------------------
if __name__ == "__main__":

    predictor = CrowdDensityPredictor()

    result = predictor.predict(
        node_id="NODE_001",
        hour=14,
        avg_duration=1800,
        total_bytes=1000000
    )

    print(
        f"Predicted Crowd Density: "
        f"{result} users"
    )
