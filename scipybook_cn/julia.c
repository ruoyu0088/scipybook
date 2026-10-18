#include <complex.h>
#include <stdlib.h>

void julia_set(double cr, double ci, double complex * arr, int n)
{
    int i;
    double complex c;
    double complex z;
    c = cr + ci * I;
    z = 0.0;
    for(i=0; i<n; i++){
        z = csqrt(z - c);
        if(rand() & 0x01){
            z = -z;
        }
        arr[i] = z;
    }
}
