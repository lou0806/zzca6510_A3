from pulp import LpMinimize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD

## Employee and role data
jobs = ["A5","A6","Man"] # Permanent staff types: APS5, APS6, Managers
contractor_vector = ["Con", "ExC"] # Contractor staff types: Contractors, Expert Contractors
streams_vector = ["Ana","Tech"] # Streams: Analysts, Technicians
level = ["1", "2", "3"] # Levels: 1,2,3

# Create the model object
model = LpProblem("Employee_Structure_Optimisation", LpMinimize)

## Decision variables - create dictionaries
# DECISION (HIRING) - an employee goes into a job and a stream
hired = {(job,stream): LpVariable(f"hired_{job}_{stream}",0,None,cat="Integer") for job in jobs for stream in streams_vector}
# DECISION (CROSS-TRAINING) - an employee at a certain job goes from one stream to another stream
trained = {(job,from_stream,to_stream): LpVariable(f"trained_{job}_{from_stream}_{to_stream}",0,None,cat="Integer") for job in jobs for from_stream in streams_vector for to_stream in streams_vector if from_stream != to_stream}
# DECISION (PROMOTION) - an employee goes from one job to another job, within a defined stream
promoted = {(from_job,to_job,stream): LpVariable(f"promoted_{from_job}_{to_job}_{stream}",0,None,cat="Integer") for from_job in jobs for to_job in jobs for stream in streams_vector if (from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man") }
# DECISION (BUY CONTRACTOR) - a contractor type goes into a stream
bought_contractor = {(Contractor, stream) : LpVariable(f"bought_{Contractor}_{stream}",0,None,cat="Integer") for Contractor in contractor_vector for stream in streams_vector}

## Constraint values.
## Here, we can adjust values for sensitivity testing
# BUDGET:
staff_budget = 10000000
services_budget = 6000000
# COSTS OF DECISIONS:
training_cost = 1000
promo_cost = 200
hiring_cost = 5000
# SALARIES (based on top of 2024 Department of Home Affairs Bands)
A5_sal  =  91809
A6_sal  =  107713
Man_sal =  134865
Con_sal =  200000
ExC_sal =  450000

sal_costs_dict = {
    "A5": A5_sal
    , "A6": A6_sal
    , "Man": Man_sal
}

hiring_costs_dict = {
    "A5": A5_sal + hiring_cost
    , "A6": A6_sal+hiring_cost
    , "Man": Man_sal+hiring_cost
}

training_costs_dict = {
    "A5": A5_sal + training_cost
    , "A6": A6_sal+training_cost
    , "Man": Man_sal+training_cost
}

promotion_costs_dict = {
    "A5": A5_sal + promo_cost
    , "A6": A6_sal + promo_cost
    , "Man": Man_sal + promo_cost
}

contractor_hired_dict = {
    "Con": Con_sal
    , "ExC" : ExC_sal
}

model += lpSum(
    hiring_costs_dict[job] * hired[job,stream] + 
    training_costs_dict[job] * trained[job,from_stream,to_stream] +
    promotion_costs_dict[job] * promoted[from_job,to_job,stream] + 
    contractor_hired_dict[Contractor] * bought_contractor[Contractor,stream]
    for job in jobs for from_job in jobs for to_job in jobs for stream in streams_vector for from_stream in streams_vector for to_stream in streams_vector for Contractor in contractor_vector
    if from_stream != to_stream and ((from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man"))
), "Minimize_Cost"


# Budget contraints
model += lpSum(
    hiring_costs_dict[job] * hired[job,stream] + 
    training_costs_dict[job] * trained[job,from_stream,to_stream] +
    promotion_costs_dict[job] * promoted[from_job,to_job,stream]
    for job in jobs for from_job in jobs for to_job in jobs for stream in streams_vector for from_stream in streams_vector for to_stream in streams_vector
    if from_stream != to_stream and ((from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man"))
) <= staff_budget

model += lpSum( 
    contractor_hired_dict[Contractor] * bought_contractor[Contractor,stream]
    for Contractor in contractor_vector for stream in streams_vector
) <= services_budget

# Workforce target
existing_employees = {("A5", "Ana"): 20, ("A5", "Tech"): 7
    , ("A6", "Ana"): 10, ("A6", "Tech"): 3
    , ("Man", "Ana"): 6, ("Man", "Tech"): 5
    , ("Con", "Ana") : 5, ("Con", "Tech") : 30
    , ("ExC","Ana") : 0, ("ExC","Tech") : 2
  }  # Example data

target_employees = {("1","Ana"): 40, ("2","Ana"): 15,("3","Ana"): 10,
    ("1","Tech"): 50,("2","Tech"): 15,("3","Tech"): 8}  # Target workforce

model += existing_employees[("A5", "Ana")] + existing_employees[("Con", "Ana")] + hired[("A5","Ana")] + trained[("A5","Tech","Ana")] + bought_contractor["Con","Ana"] - trained[("A5","Ana","Tech")] - promoted[("A5","A6","Ana")] >= target_employees[("1","Ana")]

model += existing_employees[("A6", "Ana")] + existing_employees[("ExC", "Ana")] + hired[("A6","Ana")] + trained[("A6","Tech","Ana")] + promoted[("A5","A6","Ana")] + bought_contractor["ExC","Ana"] - trained[("A6","Ana","Tech")] - promoted[("A6","Man","Ana")]>= target_employees[("2","Ana")]

model += existing_employees[("Man", "Ana")] + hired[("Man","Ana")] + trained[("Man","Tech","Ana")] + promoted[("A6","Man","Ana")] + bought_contractor["ExC","Ana"] - trained[("Man","Ana","Tech")] >= target_employees[("3","Ana")]

model += existing_employees[("A5", "Tech")] + existing_employees[("Con", "Tech")] + hired[("A5","Tech")] + trained[("A5","Ana","Tech")] + bought_contractor["Con","Tech"]  - trained[("A5","Tech","Ana")] - promoted[("A5","A6","Tech")]>= target_employees[("1","Tech")]

model += existing_employees[("A6", "Tech")] + existing_employees[("ExC", "Tech")]  + hired[("A6","Tech")] + trained[("A6","Ana","Tech")] + promoted[("A5","A6","Tech")] - trained[("A6","Tech","Ana")] - promoted[("A6","Man","Tech")]>= target_employees[("2","Tech")]

model += existing_employees[("Man", "Tech")] + hired[("Man","Tech")] + trained[("Man","Ana","Tech")] + promoted[("A6","Man","Tech")] - trained[("Man","Tech","Ana")] >= target_employees[("3","Tech")]

model += existing_employees[("A5", "Tech")] - trained[("A5","Tech","Ana")] >= 0
model += existing_employees[("A5", "Ana")] - trained[("A5","Ana","Tech")]  >= 0
model += existing_employees[("A6", "Tech")] - trained[("A6","Tech","Ana")] >= 0
model += existing_employees[("A6", "Ana")] - trained[("A6","Ana","Tech")]  >= 0
model +=  existing_employees[("Man", "Tech")] - trained[("Man","Tech","Ana")]  >= 0
model +=  existing_employees[("Man", "Ana")] - trained[("Man","Ana","Tech")]  >= 0

#model += lpSum(promoted["A5","A6",stream] for stream in streams_vector) <= promotion_limit
#model += lpSum(promoted["A6","Man",stream] for stream in streams_vector) <= promotion_limit

model.solve(PULP_CBC_CMD(timeLimit=60))

print("Optimal Hiring, Training, and Promotion Plan:")
for job in jobs:
    for stream in streams_vector:
        print(f"{job} {stream}: Hired = {hired[job, stream].varValue}")

for job in jobs:
    for from_stream in streams_vector:
        for to_stream in streams_vector:
            if from_stream != to_stream:
                print(f"{job} {from_stream} {to_stream}: Trained = {trained[job, from_stream, to_stream].varValue}")

for from_job in jobs:
    for to_job in jobs:
        for stream in streams_vector:
            if (from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man"):
                print(f"{from_job} {to_job} {stream}: Promoted = {promoted[from_job, to_job, stream].varValue}")

for contractor in contractor_vector:
    print(f"{contractor} {stream} : Bought contractor = {bought_contractor[contractor, stream].varValue}")
