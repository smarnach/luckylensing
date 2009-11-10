#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include "ll.c"

#define XPIXELS 1024
#define YPIXELS 512

int main(int argc, char *argv[])
{
    const unsigned N = XPIXELS*YPIXELS;
    struct ll_lens_t lens[3] = {{0.0, 0.0,  1.},
                                   {1.2, 0.0,  2e-2},
                                   {1.2, 0.025, 4e-3}};
    struct ll_lenses_t lenses = {3, lens};
    struct ll_rect_t region = {.26, -.05, .46, .05};
    struct ll_magpattern_param_t params;
    ll_init_magpattern_params(&params, &lenses, &region, XPIXELS, YPIXELS);
    struct ll_rect_t rect = {-1., -.25, 1.5, .25};
    double progress;
    int *magpat = calloc(N, sizeof(int));
    char *buf = calloc(N, sizeof(char));

    printf("Calculating magnification pattern...\n");
    clock_t t = clock();
    ll_rayshoot(&params, magpat, &rect, 300, 60, 3, &progress);
    printf("finished in %g seconds.\n", (double)(clock()-t)/CLOCKS_PER_SEC);

    printf("Converting to an image...\n");
    t = clock();
    ll_image_from_magpat(buf, magpat, N);
    printf("finished in %g seconds.\n", (double)(clock()-t)/CLOCKS_PER_SEC);

    if (argc > 1)
    {
        FILE *f = fopen(argv[1], "w");
        fwrite(buf, sizeof(char), N, f);
        fclose(f);
    }
}
