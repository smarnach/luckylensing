#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include "ll.h"

int main(int argc, char *argv[])
{
    const int xpixels = 1024;
    const int ypixels = 512;
    const unsigned N = xpixels*ypixels;
    const unsigned levels = 3;
    const int xrays = 600;
    const int yrays = 120;
    struct ll_rect_t rect = {-1., -.25, 2.5, .5};

    struct ll_lens_t lens[3] = {{0.0, 0.0,  1.},
                                {1.2, 0.0,  4e-4},
                                {1.2, 0.025, 2.5e-5}};
    struct ll_lenses_t lenses = {3, lens};
    struct ll_rect_t region = {.26, -.05, .2, .1};

    struct ll_magpattern_param_t params;
    ll_init_magpattern_params(&params, &lenses, &region, xpixels, ypixels);
    struct ll_rayshooter_t rs;
    ll_init_rayshooter(&rs, &params, levels);
    double progress;
    int *magpat = calloc(N, sizeof(int));
    char *buf = calloc(N, sizeof(char));

    printf("Calculating magnification pattern...\n");
    clock_t t = clock();
    ll_rayshoot(&rs, magpat, &rect, xrays, yrays, &progress);
    printf("finished in %g seconds.\n", (double)(clock()-t)/CLOCKS_PER_SEC);

    double density = xrays*yrays;
    for (unsigned i = 0; i < levels-2; ++i)
        density *= rs.refine * rs.refine;
    density *= rs.refine_final * rs.refine_final;
    density /= N;
    density *= region.width * region.height / rect.width * rect.height;
    printf("Average rays per pixel shot:    %8.2f\n", density);

    double avg = 0.0;
    for (unsigned i = 0; i < N; ++i)
        avg += magpat[i];
    avg /= N;
    printf("Average rays per pixel counted: %8.2f\n", avg);
    printf("Average magnification:          %8.2f\n", avg/density);

    printf("Converting to an image...\n");
    t = clock();
    ll_render_magpattern_greyscale(buf, magpat, N);
    printf("finished in %g seconds.\n", (double)(clock()-t)/CLOCKS_PER_SEC);

    if (argc > 1)
    {
        FILE *f = fopen(argv[1], "w");
        fwrite(buf, sizeof(char), N, f);
        fclose(f);
    }
}
