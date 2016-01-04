
/* Created: 9/17/2015, property of YouthTruth

	Import: CSV file with columns: StudentID, teachername, teacherfirst, teacherlast, TeacherID, subject, coursename
	run with two arguments: (1) roster data CSV file name (2) export - usually school short - name for class summary
    A summary version which lists the number of students in each teachername, coursename combination is created

	 
*/

version 12  //created with STATA version 12

//arguments for import and export files
args import export
display " arguments are `import' and `export' " 

insheet using "`import'" , comma names case
bysort TeacherID coursename: gen StudentCount=_N
sort TeacherID coursename
quietly by TeacherID coursename: gen dup = cond(_N==1,0,_n)
drop if dup>1
sort StudentCount
outsheet teacherfirst teacherlast TeacherID coursename StudentCount using "`export'", comma replace
clear
