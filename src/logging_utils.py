
def print_bar():
    """
    Function that will print a process bar
    :return:
    """
    print("=" * 40)

def print_bar(length=200, char='█'):
    """
    Print a horizontal bar with a given length and character.

    :param length: Length of the bar to be printed
    :param char: Character to use for printing the bar
    """
    print(char * length)


def print_file_analysis_start(commit_hash):
    """
    Function that will print a bar and what file that it is analysing.

    :param commit_hash: of the commit that is being analyzed
    :return:
    """
    print_bar()
    print(f"\nAnalyzing {commit_hash}\n")


def print_commit_analysis_start(commit, commit_count, repo_url):
    """
    Function that will print where in the process the system is.

    This is to easier keep track of the analysis and debugging

    :param commit: The commit hash that will be analysed
    :param commit_count: The number of commits that has been analysed
    :param repo_url: The URL of the repo to analyze
    :return:
    """
    print_bar()
    print(f"\nAnalyzing Commit: {commit.hash} in {repo_url}\n")
    print(f"\nStarting on Commit no: {commit_count}\n")