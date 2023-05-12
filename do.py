# input list
results = [[[[1105, 2, 3, 11],[1405, 5, 6, 12]],7,8,9],[[[1, 2, 3, 11],[4, 5, 6, 12]],7,8,9]]
print(len(results[0][0]))
def averaging_lambda_results(results):
    signal_dates = []
    risk95_values = []
    risk99_values = []
    pnl_values = []

    for i in range(len(results)):
        signal_dates.append(results[0][0][i][0])
        
    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            print(result[0][i][1])
            avg = avg + result[0][i][1]
        avg = avg / len(results)

        risk95_values.append(avg)

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            print(result[0][i][2])
            avg = avg + result[0][i][2]
        avg = avg / len(results)

        risk99_values.append(avg)

    for i in range(len(results[0][0])):
        avg = 0
        for result in results:
            print(result[0][i][3])
            avg = avg + result[0][i][3]
        avg = avg / len(results)

        pnl_values.append(avg)

    # print(signal_dates)
    result_list = [['Signal Date', 'Risk 95%', 'Risk 99%', 'Profit/Loss per Share']]
    for i in range(len(signal_dates)):
        result_list.append([signal_dates[i], risk95_values[i], risk99_values[i], pnl_values[i]])

        # calculate the total profit/loss and average risk values
    total_pnl = sum(pnl_values)
    avg_var95 = sum(risk95_values) / len(risk95_values)
    avg_var99 = sum(risk99_values) / len(risk99_values)

    print([result_list, total_pnl, avg_var95, avg_var99])
    return (result_list, total_pnl, avg_var95, avg_var99)
# for j in range(len(results[0][0])):
#     for i in range(len(results)):
#         print(results[i][0][j][1])

# # Initialize the list to store the averaged values
# alpha_values = []

# # loop through each element of the results list
# for i in range(len(results)):
#     if isinstance(results[i], list):
#         # if the element is a list, loop through each element of the sublist
#         for j in range(len(results[i])):
#             if isinstance(results[i][j], list):
#                 # if the element is a nested list, loop through each element of the sub-sublist
#                 for k in range(len(results[i][j])):
#                     # if isinstance(results[i][j][k], str):
#                         # if the element is a string, append it to the alpha_values list
#                     alpha_values.append(results[i][j][k])

# print(alpha_values)

# # Initialize empty lists to store the averages
# avg2_list = []
# avg5_list = []

# # Loop over the length of results[0][0]
# for i in range(len(results[0][0])):
#     # Initialize sum variables for each sublist
#     sum2 = 0
#     sum5 = 0
#     count2 = 0
#     count5 = 0
    
#     # Loop over each sublist in results
#     for j in range(len(results)):
#         sublist = results[j][0][i]
#         print(sublist)
#         # Calculate the average of the 2nd and 5th values in the sublist, if they exist
#         if len(sublist) >= 2:
#             sum2 += sublist[1]
#             count2 += 1
#         if len(sublist) >= 5:
#             sum5 += sublist[4]
#             count5 += 1
    
#     # Calculate the averages for the current sublist
#     avg2 = sum2 / count2 if count2 > 0 else 0
#     avg5 = sum5 / count5 if count5 > 0 else 0
    
#     # Append the averages to the corresponding lists
#     avg2_list.append(avg2)
#     avg5_list.append(avg5)

# # Print the resulting lists
# print("risk95_values:", avg2_list)
# print("risk99_values:", avg5_list)

