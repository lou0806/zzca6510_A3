from pulp import LpMinimize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD, value

## Employee and role data
jobs = ["A5","A6","Man"] # Permanent staff types: APS5, APS6, Managers
contractor_vector = ["Con", "ExC"] # Contractor staff types: Contractors, Expert Contractors
streams_vector = ["Ana","Tech"] # Streams: Analysts, Technicians
level = ["1", "2", "3"] # Levels: 1,2,3

# Create the model object
model = LpProblem("Employee_Structure_Optimisation", LpMinimize)

## Decision variables - create dictionaries
# DECISION (HIRING) - an employee goes into a job and a stream
hired = {(job,stream): LpVariable(f"hired_{job}_{stream}",lowBound=0,cat="Integer") for job in jobs for stream in streams_vector}
# DECISION (CROSS-TRAINING) - an employee at a certain job goes from one stream to another stream
trained = {(job,from_stream,to_stream): LpVariable(f"trained_{job}_{from_stream}_{to_stream}",lowBound=0,cat="Integer") for job in jobs for from_stream in streams_vector for to_stream in streams_vector if from_stream != to_stream}
# DECISION (PROMOTION) - an employee goes from one job to another job, within a defined stream
# Note: here, we have to create a dummy variable {"A5","A5",stream} to make the rest of the code work
promoted = {(from_job,to_job,stream): LpVariable(f"promoted_{from_job}_{to_job}_{stream}",lowBound=0,cat="Integer") for from_job in jobs for to_job in jobs for stream in streams_vector if (from_job == "A5" and to_job == "A5") or (from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man") }
# DECISION (BUY CONTRACTOR) - a contractor type goes into a stream
bought_contractor = {(Contractor, stream) : LpVariable(f"bought_{Contractor}_{stream}",lowBound=0,cat="Integer") for Contractor in contractor_vector for stream in streams_vector}

## Constraint values.
## Here, we can adjust values for sensitivity testing
# BUDGET:
staff_budget = 6000000
services_budget = 4000000
# COSTS OF DECISIONS:
training_cost = 1
promo_cost = 2
hiring_cost = 20000
# SALARIES (based on top of 2024 Department of Home Affairs Bands)
A5_sal  =  91809
A6_sal  =  107713
Man_sal =  134865
Con_sal =  200000
ExC_sal =  450000
# EXISTING WORKFORCE
existing_employees = {("A5", "Ana"): 20, ("A5", "Tech"): 7
    , ("A6", "Ana"): 10, ("A6", "Tech"): 3
    , ("Man", "Ana"): 6, ("Man", "Tech"): 5
    , ("Con", "Ana") : 5, ("Con", "Tech") : 30
    , ("ExC","Ana") : 0, ("ExC","Tech") : 2
  }
# TARGET WORKFORCE (by level)
target_employees = {("1","Ana"): 40, ("2","Ana"): 20,("3","Ana"): 10,
    ("1","Tech"): 50,("2","Tech"): 20,("3","Tech"): 10}

## Define the dictionaries of costs: salary costs, hiring costs, training costs, promotion costs and contractors
sal_costs_dict = {
    "A5": A5_sal
    , "A6": A6_sal
    , "Man": Man_sal
}

hiring_costs_dict = {
    "A5": A5_sal + hiring_cost
    , "A6": A6_sal + hiring_cost
    , "Man": Man_sal + hiring_cost
}

training_costs_dict = {
    "A5": A5_sal + training_cost - A5_sal
    , "A6": A6_sal + training_cost - A6_sal
    , "Man": Man_sal + training_cost - Man_sal
}

promotion_costs_dict = {
    "A5": A5_sal + promo_cost - A5_sal
    , "A6": A6_sal + promo_cost - A5_sal
    , "Man": Man_sal + promo_cost - A6_sal
}

contractor_hired_dict = {
    "Con": Con_sal
    , "ExC" : ExC_sal
}

## Define the objective function - minimising the spend
model += (lpSum(
        hiring_costs_dict[job] * hired[job,stream] + 
        training_costs_dict[job] * trained[job,from_stream,to_stream] +
        promotion_costs_dict[job] * promoted[from_job,to_job,stream]
        for job in jobs for from_job in jobs for to_job in jobs for stream in streams_vector for from_stream in streams_vector for to_stream in streams_vector
        if (from_stream != to_stream and ((from_job == "A5" and to_job == "A5") or (from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man")) and job == to_job and to_stream == stream)
    )
    + lpSum(
        contractor_hired_dict[Contractor] * bought_contractor[Contractor,stream]
        for Contractor in contractor_vector for stream in streams_vector
    ), "Minimize_Cost")

#print(promoted)

## Define the constraints
# CONSTRAINT: Cost of hiring, promoting, training permanent staff is lower than Permanent Staff Budget
model += (lpSum(
    hiring_costs_dict[job] * hired[job,stream] + 
    training_costs_dict[job] * trained[job,from_stream,to_stream] +
    promotion_costs_dict[job] * promoted[from_job,to_job,stream]
    for job in jobs for from_job in jobs for to_job in jobs for stream in streams_vector for from_stream in streams_vector for to_stream in streams_vector
    if (from_stream != to_stream and ((from_job == "A5" and to_job == "A5") or (from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man")) and job == to_job and to_stream == stream)
) <= staff_budget, "Staff budget constraint")

# CONSTRAINT: Cost of buying contractors is lower than Contractor Budget
model += (lpSum(
    contractor_hired_dict[Contractor] * bought_contractor[Contractor,stream]
    for Contractor in contractor_vector for stream in streams_vector
) <= services_budget, "Contractor budget constraint")

# CONSTRAINTS: Each level hits the target workforce
model += (existing_employees[("A5", "Ana")] + existing_employees[("Con", "Ana")] + hired[("A5","Ana")] + trained[("A5","Tech","Ana")] + bought_contractor["Con","Ana"] - trained[("A5","Ana","Tech")] - promoted[("A5","A6","Ana")] >= target_employees[("1","Ana")],"Target Level 1 Analysts")
model += (existing_employees[("A6", "Ana")] + existing_employees[("ExC", "Ana")] + hired[("A6","Ana")] + trained[("A6","Tech","Ana")] + promoted[("A5","A6","Ana")] + bought_contractor["ExC","Ana"] - trained[("A6","Ana","Tech")] - promoted[("A6","Man","Ana")]>= target_employees[("2","Ana")],"Target Level 2 Analysts")
model += (existing_employees[("Man", "Ana")] + hired[("Man","Ana")] + trained[("Man","Tech","Ana")] + promoted[("A6","Man","Ana")] - trained[("Man","Ana","Tech")] >= target_employees[("3","Ana")], "Target Level 3 Analysts")
model += (existing_employees[("A5", "Tech")] + existing_employees[("Con", "Tech")] + hired[("A5","Tech")] + trained[("A5","Ana","Tech")] + bought_contractor["Con","Tech"]  - trained[("A5","Tech","Ana")] - promoted[("A5","A6","Tech")] >= target_employees[("1","Tech")], "Target Level 1 Tech")
model += (existing_employees[("A6", "Tech")] + existing_employees[("ExC", "Tech")]  + hired[("A6","Tech")] + trained[("A6","Ana","Tech")] + promoted[("A5","A6","Tech")] + bought_contractor["ExC","Tech"] - trained[("A6","Tech","Ana")] - promoted[("A6","Man","Tech")]>= target_employees[("2","Tech")], "Target Level 2 Tech")
model += (existing_employees[("Man", "Tech")] + hired[("Man","Tech")] + trained[("Man","Ana","Tech")] + promoted[("A6","Man","Tech")] - trained[("Man","Tech","Ana")] >= target_employees[("3","Tech")], "Target Level 3 Tech")
# CONSTRAINT: Force the number of 'promotions' of A5 to A5 to be 0 - this is to ensure the dictionaries function properly
model += (promoted[("A5","A5","Ana")] == 0)
model += (promoted[("A5","A5","Tech")] == 0)
# CONSTRAINTS: Cannot train and promote more employees than there originally exists
model += trained[("A5","Tech","Ana")] + promoted[("A5","A6","Tech")] <= existing_employees[("A5", "Tech")]
model += trained[("A5","Ana","Tech")] + promoted[("A5","A6","Ana")] <= existing_employees[("A5", "Ana")]
model += trained[("A6","Tech","Ana")] + promoted[("A6","Man","Ana")] <= existing_employees[("A6", "Tech")]
model += trained[("A6","Ana","Tech")] + promoted[("A6","Man","Tech")] <= existing_employees[("A6", "Ana")]
model +=  trained[("Man","Tech","Ana")] <= existing_employees[("Man", "Tech")] 
model +=  trained[("Man","Ana","Tech")] <= existing_employees[("Man", "Ana")]


## Solve the model and print outputs
model.solve(PULP_CBC_CMD(timeLimit=120))

# Print model constraints
for name, constraint in model.constraints.items():
    print(f"{name}: {constraint}")

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
    for stream in streams_vector:
        print(f"{contractor} {stream} : Bought contractor = {bought_contractor[contractor, stream].varValue}")

cost = value(model.objective)  
print(f"Cost to budget: {cost} out of {staff_budget+services_budget}")
print(f"We have remaining: {staff_budget+services_budget-cost}")


staff_budget_spend = value(
    lpSum(
        hiring_costs_dict[job] * hired[job,stream] + 
        training_costs_dict[job] * trained[job,from_stream,to_stream] +
        promotion_costs_dict[job] * promoted[from_job,to_job,stream]
        for job in jobs for from_job in jobs for to_job in jobs for stream in streams_vector for from_stream in streams_vector for to_stream in streams_vector
        if (from_stream != to_stream and ((from_job == "A5" and to_job == "A5") or (from_job == "A5" and to_job == "A6") or (from_job == "A6" and to_job == "Man")) and job == to_job and to_stream == stream)
    )
)

services_budget_spend = value(
    lpSum(
        contractor_hired_dict[Contractor] * bought_contractor[Contractor,stream]
        for Contractor in contractor_vector for stream in streams_vector
    )
)

print(f"Staff budget spend: {staff_budget_spend}")
print(f"Remaining Staff budget: {staff_budget - staff_budget_spend}")
print(f"Services budget spend: {services_budget_spend}")
print(f"Remaining Services budget: {services_budget - services_budget_spend}")


#print(model.objective)