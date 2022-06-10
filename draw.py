import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta

def format_time(n = 15):
    # Given timestamp in string
    time_str = '05/17/2021 00:00:00'
    date_format_str = '%m/%d/%Y %H:%M:%S'
    # create datetime object from timestamp string
    given_time = datetime.strptime(time_str, date_format_str)
    #print('Given timestamp: ', given_time)
    # Add 15 minutes to datetime object
    final_time = given_time + timedelta(seconds=n)
    #print('Final Time (15 minutes after given time ): ', final_time)
    # Convert datetime object to string in specific format
    final_time_str = final_time.strftime('%m/%d/%Y %H:%M:%S')
    #print('Final Time as string object: ', final_time_str)
    return  final_time_str

    
def draw_gannt(job_stats = None):
    y_start = 10
    no_of_colors = 2
    colors = ['tab:red', 'tab:green']

    fig, ax = plt.subplots()
    labels:list[str] = []
    maxX = 0
    minX = 1e20
    yTicks = []
    y_tick_start = 15

    for job_id, stats in job_stats.items():
        labels.append(f'job {job_id}')
        # build xranges for this job
        x_ranges = []
        job_color = []
        for stage_stat in stats:
            x_ranges.append((stage_stat[1], stage_stat[2]))
            #print(f'stage {stage_stat[0]} color {colors[stage_stat[0]]}')
            job_color.append(colors[stage_stat[0]])
            maxX = max(maxX, stage_stat[1] + stage_stat[2])
            minX = min(minX, stage_stat[1])
        y_range = (y_start, 9)
        ax.broken_barh(x_ranges, y_range, facecolors=job_color)
        y_start = y_start + 10
        yTicks.append(y_tick_start)
        y_tick_start = y_tick_start + 10
    ax.set_ylim(5, y_tick_start + 10)
    ax.set_xlim(minX, maxX)
    ax.set_xlabel('seconds since start')
    ax.set_yticks(yTicks)
    ax.set_yticklabels(labels)
    ax.grid(True)
    ax.set_title("'stage 0: red, stage 1: green'")


    #no_of_colors = len(x_pairs)

    #         for j in range(no_of_colors)]

    #xranges: sequence of tuples(xmin, xwidth Thex - positions and extendof the rectangles.For each tuple(xmin, xwidth) arectangle is drawnfrom xmin to xmin + xwidth.

    #yranges: (ymin, ymax)The y - position and extend for all the rectangles.
    # broken_barh([xrange], yranges]

    #ax.broken_barh([(110, 30), (150, 10)], (10, 9), facecolors='tab:blue')
    #ax.broken_barh([(10, 50), (100, 20), (130, 10)], (20, 9),
    #               facecolors=('tab:orange', 'tab:green', 'tab:red'))


    plt.show()
    #plt.show()