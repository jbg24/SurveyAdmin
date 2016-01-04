/* Created: 9/17/2015, property of YouthTruth

	Import: excel file with columns: StudentID, teachername, teacherfirst, teacherlast, TeacherID, subject, coursename
	run with two arguments: (1) roster data CSV file name (2) export - usually school short - name for class summary
    A pivoted long-to-wide copy to the roster data (basename_restructured.xls)

*/

version 12  //created with STATA version 12

//arguments for import and export files
args import export
display " arguments are `import' and `export' " 

insheet using "`import'" , comma names case
bysort StudentID: gen order = _n
reshape wide coursename TeacherID teacherlast teacherfirst teachername subject, i(StudentID) j(order)
outsheet using "`export'", comma replace
clear
