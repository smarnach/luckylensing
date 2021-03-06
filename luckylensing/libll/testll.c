// Lucky Lensing Library (http://github.com/smarnach/luckylensing)
// Copyright 2010 Sven Marnach

#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ll.h"

int main(int argc, char *argv[])
{
    const int xpixels = 1024;
    const int ypixels = 512;
    const unsigned N = xpixels*ypixels;
    const unsigned levels = 3;
    const int xrays = 600;
    const int yrays = 120;
    struct ll_rect rect = {-1., -.25, 2.5, .5};

    struct ll_lens lens[3] = {{0.0, 0.0,  1.},
                              {1.2, 0.0,  4e-4},
                              {1.2, 0.025, 2.5e-5}};
    struct ll_lenses lenses = {3, lens};
    struct ll_rect region = {.26, -.05, .2, .1};

    struct ll_magpat_params params;
    ll_init_magpat_params(&params, &lenses, &region, xpixels, ypixels);
    struct ll_rayshooter rs;
    ll_init_rayshooter(&rs, &params);
    double progress;
    float *magpat = calloc(N, sizeof(float));
    unsigned char *buf = calloc(3*N, sizeof(char));
    const unsigned char colors[9][3] = {{0, 0, 0}, {64, 0, 128}, {0, 0, 255},
                                        {0, 255, 255}, {0, 255, 0}, {255, 255, 0},
                                        {255, 0, 0}, {255, 0, 255},
                                        {255, 255, 255}};
    const unsigned steps[9] = {128, 255, 255, 255, 255, 255, 255, 255, 0};

    for (rs.kernel = LL_KERNEL_BILINEAR;
         rs.kernel <= LL_KERNEL_TRIANGULATED; ++rs.kernel)
    {
        if (rs.kernel == LL_KERNEL_BILINEAR)
            printf("Using bilinear ray shooting\n");
        else if (rs.kernel == LL_KERNEL_TRIANGULATED)
            printf("Using triangulated ray shooting\n");
        else
            continue;

        memset(magpat, 0, N * sizeof(float));
        printf("Calculating magnification pattern...\n");
        clock_t t = clock();
        ll_rayshoot(&rs, magpat, &rect, xrays, yrays, levels, &progress);
        printf("finished in %g seconds.\n", (double)(clock()-t)/CLOCKS_PER_SEC);

        double density = xrays*yrays;
        for (unsigned i = 0; i < levels-2; ++i)
            density *= rs.refine * rs.refine;
        density *= rs.refine_kernel * rs.refine_kernel;
        density /= N;
        density *= region.width * region.height / (rect.width * rect.height);
        printf("Average rays per pixel shot:    %8.2f\n", density);

        double avg = 0.0;
        for (unsigned i = 0; i < N; ++i)
            avg += magpat[i];
        avg /= N;
        printf("Average magnification:          %8.2f\n", avg);

        printf("Converting to an image...\n");
        t = clock();
        ll_render_magpat_gradient(magpat, buf, xpixels, ypixels,
                                  -1.0, -1.0, colors, steps);
        printf("finished in %g seconds.\n\n", (double)(clock()-t)/CLOCKS_PER_SEC);
    }

    if (argc > 1)
    {
        FILE *f = fopen(argv[1], "w");
        fwrite(buf, sizeof(char), 3*N, f);
        fclose(f);
    }
}
