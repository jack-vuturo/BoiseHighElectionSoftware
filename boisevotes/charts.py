class ChartJS:
  id = ""
  chart_type = "line"
  title = ""
  data = []
  labels = []

  def __init__(self, id, title, chart_type):
    self.id = id
    self.title = title
    self.chart_type = chart_type

class ChartDataSet:
  name = ""
  data = []
  color = "#0ff"

  def __init__(self, name, color, data):
    self.name = name
    self.color = color
    self.data = data