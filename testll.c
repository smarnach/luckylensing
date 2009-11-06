#include "ll.c"

#define XPIXELS 1024
#define YPIXELS 512

struct ll_lens_type lens[3] = {{0.0, 0.0,  1.},
                               {1.2, 0.0,  2e-2},
                               {1.2, 0.025, 4e-3}};
struct ll_lenses_type lenses = {3, lens};
struct ll_rect_type region = {.26, -.05, .46, .05};
int magpat[XPIXELS*YPIXELS];

int main()
{
    struct ll_magpattern_param_type params
        = {lenses, region, XPIXELS, YPIXELS, 0.0, 0.0};
    struct ll_rect_type rect = {-1., -.25, 1.5, .25};
    double progress;
    ll_rayshoot(&params, magpat, &rect, 250, 50, 2, &progress);
}
