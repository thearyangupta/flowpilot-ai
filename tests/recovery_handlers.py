class RecordingHandler:
    def __init__(self, value: str):
        self.value = value
        self.calls = 0

    def __call__(self, context, config):
        self.calls += 1

        result = context.copy()
        result[config["output_key"]] = self.value

        return result