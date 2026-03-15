from google import genai

# Initialize client with your valid API key
client = genai.Client(api_key="AIzaSyCUwgRBCSYFlg6AplFeyYRgqeT7k-SfAng")

# List models correctly
models = client.models.list()  # returns a Pager object

for m in models:  # iterate directly over the Pager
    print(m.name, "-", getattr(m, "description", "No description"))