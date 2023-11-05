import streamlit as st
import pandas as pd

from ortools.sat.python import cp_model

"""Take input for given values outside and inside grid"""

n = 5

outer_inputs = {
    "top": [2,0,3,0,0],
    "left": [0,3,0,0,0],
    "right": [0,0,0,0,3],
    "bottom": [2,0,2,4,3]
    }

grid_inputs = [[2,0,2]]


def set_up_booleans(n, model, grid, visible, blocking, angle):

  # loop over each row
  for i in range(n):

    # if angle is right or bottom, need to loop from high to low
    if angle == "left" or angle == "top":
      range_j = range(1,n)
    else:
      range_j = reversed(range(0,n-1))

    # loop over each column to check for visibility
    # (note that column 0 is always visible from the left so no boolean needed
    # for j = 0)
    for j in range_j:
      # These booleans represent whether a skyscraper is visible from the left
      visible[(i,j, angle)] = model.NewBoolVar("")

      # if angle is right or bottom, need to loop from high to low
      if angle == "left" or angle == "top":
        range_k = range(j)
      else:
        range_k = range(j+1,n)

      for k in range_k:

        if angle == "left" or angle == "right":
          row_i = i
          row_k = i
          col_j = j
          col_k = k
        else:
          row_i = j
          row_k = k
          col_j = i
          col_k = i

        # enforce all towers left of col j to be less than it if col j visible (2)
        model.Add(grid[(row_k,col_k)] < grid[(row_i,col_j)]).OnlyEnforceIf(visible[(i,j, angle)])

        # these represent whther a column k tower blocks col j tower
        blocking[(i,j,k, angle)] = model.NewBoolVar("")

        # enforce the condition of col k blocking col j
        model.Add(grid[(row_k,col_k)] > grid[(row_i,col_j)]).OnlyEnforceIf(blocking[(i,j,k, angle)])
        model.Add(grid[(row_k,col_k)] < grid[(row_i,col_j)]).OnlyEnforceIf(blocking[(i,j,k, angle)].Not())

      # must be at least one blocking tower if col j not visible
      model.Add(sum([blocking[(i,j,k, angle)] for k in range_k]) > 0).OnlyEnforceIf(visible[(i,j, angle)].Not())

def main():

  values = range(1, n+1)
  rows = range(n)
  cols = range(n)

  model = cp_model.CpModel()

  # generic latin square rules =================================================

  # initialise n by n grid that can take integrs from 1 to n
  grid = {}
  for i in rows:
    for j in cols:
      grid[(i,j)] = model.NewIntVar(1, n, f"grid[i{i},j{j}]")

  # enforce each row to contain one of each number
  for i in rows:
    model.AddAllDifferent(grid[(i,j)] for j in cols)
  # enforce each column to contain one of each number
  for j in cols:
    model.AddAllDifferent(grid[(i,j)] for i in rows)

  # Skyscrapers specific rules =================================================

  # we need initialise of booleans
  # booleans that are true if tower i,j is visible from l/r/u/d
  visible = {}
  # booleans that are true if tower i,j is blocked by tower i,k from l/r/u/d
  blocking = {}

  for angle in ("top", "left", "right", "bottom"):

    set_up_booleans(n, model, grid, visible, blocking, angle)

    if angle == "left" or angle == "top":
      range_j = range(1,n)
    else:
      range_j = range(n-1)

    for i in range(n):
      n_visible = outer_inputs[angle][i]
      if n_visible == 0:
        continue
      else:
        # note that column 0 is always visible from the left so sum is given - 1
        model.Add(sum([visible[(i,j, angle)] for j in range_j]) == n_visible - 1)


  # Add given cells
  for i in range(len(grid_inputs)):
    model.Add(grid[(grid_inputs[i][0],grid_inputs[i][1])] == grid_inputs[i][2])

  solver = cp_model.CpSolver()
  solver.parameters.linearization_level = 0
  # Enumerate all solutions.
  solver.parameters.enumerate_all_solutions = True

  class PartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, grid, n, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._grid = grid
        self._n = n
        self._solution_count = 0
        self._solution_limit = limit

    def on_solution_callback(self):
        self._solution_count += 1
        st.write(f"Solution {self._solution_count}")
        solution_array = np.empty([n,n])
        for i in rows:
          for i in cols:
            solution_array[i][j] = self.Value(self._grid[(i,j)])

        df = pd.DataFrame(solution array, columns = ["col" + i for i in range(n)])
        components.html(df.to_html(header=False, index=False))

        if self._solution_count >= self._solution_limit:
            st.write(f"Stop search after {self._solution_limit} solutions")
            self.StopSearch()

    def solution_count(self):
        return self._solution_count

  # Display the first five solutions.
  solution_limit = 5
  solution_printer = PartialSolutionPrinter(grid, n, solution_limit)

  solver.Solve(model, solution_printer)

if __name__ == '__main__':
  main()
