#include "ll.h"
#include <values.h>
#include <math.h>
#include <stdio.h>

extern void
ll_init_magpattern_params(struct ll_magpattern_param_t *params,
                          struct ll_lenses_t *lenses,
                          struct ll_rect_t *region,
                          unsigned xpixels, unsigned ypixels)
{
    params->lenses.num_lenses = lenses->num_lenses;
    params->lenses.lens = lenses->lens;
    params->region.x0 = region->x0;
    params->region.x1 = region->x1;
    params->region.y0 = region->y0;
    params->region.y1 = region->y1;
    params->xpixels = xpixels;
    params->ypixels = ypixels;
    params->pixels_per_width = xpixels / (region->x1 - region->x0);
    params->pixels_per_height = ypixels / (region->y1 - region->y0);
}

extern void
ll_init_rayshooter(struct ll_rayshooter_t *rs,
                   struct ll_magpattern_param_t *params)
{
    rs->params = params;
    rs->refine = 15;
    rs->refine_final = 25;
    rs->cancel = false;
}

extern void
ll_cancel_rayshooter(struct ll_rayshooter_t *rs)
{
    rs->cancel = true;
}

extern bool __attribute__ ((hot))
ll_shoot_single_ray(struct ll_magpattern_param_t *params,
                    double x, double y, double *mag_x, double *mag_y)
{
    struct ll_lens_t *lens = params->lenses.lens;
    double x_deflected = x, y_deflected = y;
    for(unsigned i = 0; i < params->lenses.num_lenses; ++i)
    {
        double dx = x - lens[i].x;
        double dy = y - lens[i].y;
        double theta_squared = dx*dx + dy*dy;
        if (theta_squared == 0.0)
        {
            *mag_x = x;
            *mag_y = y;
            return false;
        }
        double deflection = lens[i].theta_E*lens[i].theta_E / theta_squared;
        x_deflected -= dx * deflection;
        y_deflected -= dy * deflection;
    }
    *mag_x = (x_deflected - params->region.x0) * params->pixels_per_width;
    *mag_y = (y_deflected - params->region.y0) * params->pixels_per_height;
    return (0 <= *mag_x && *mag_x < params->xpixels &&
            0 <= *mag_y && *mag_y < params->ypixels);
}

extern void
ll_rayshoot_rect(struct ll_magpattern_param_t *params, int *magpat,
                 const struct ll_rect_t *rect, int xrays, int yrays)
{
    double width_per_xrays = (rect->x1 - rect->x0) / xrays;
    double height_per_yrays = (rect->y1 - rect->y0) / yrays;
    double mag_x, mag_y;
    for (int j = 0; j < yrays; ++j)
        for (int i = 0; i < xrays; ++i)
            if (ll_shoot_single_ray(params,
                                    rect->x0 + i*width_per_xrays,
                                    rect->y0 + j*height_per_yrays,
                                    &mag_x, &mag_y))
                ++magpat[(int)mag_y*params->xpixels + (int)mag_x];
}

extern void __attribute__ ((hot))
ll_rayshoot_bilinear(struct ll_magpattern_param_t *params, int *magpat,
                     struct ll_rect_t *rect, int refine)
{
    double ul_x, ul_y, ur_x, ur_y, ll_x, ll_y, lr_x, lr_y;
    bool ul = ll_shoot_single_ray(params, rect->x0, rect->y0, &ul_x, &ul_y);
    bool ur = ll_shoot_single_ray(params, rect->x1, rect->y0, &ur_x, &ur_y);
    bool ll = ll_shoot_single_ray(params, rect->x0, rect->y1, &ll_x, &ll_y);
    bool lr = ll_shoot_single_ray(params, rect->x1, rect->y1, &lr_x, &lr_y);
    if (ul && ur && ll && lr)
    {
        double inv_refine = 1.0/refine;
        double ldown_x = (ll_x - ul_x) * inv_refine;
        double ldown_y = (ll_y - ul_y) * inv_refine;
        double rdown_x = (lr_x - ur_x) * inv_refine;
        double rdown_y = (lr_y - ur_y) * inv_refine;
        double right_x = (ur_x - ul_x) * inv_refine;
        double right_y = (ur_y - ul_y) * inv_refine;
        double update_x = (rdown_x - ldown_x) * inv_refine;
        double update_y = (rdown_y - ldown_y) * inv_refine;
        double sx = ul_x;
        double sy = ul_y;
        for (int j = 0; j < refine; ++j)
        {
            double x = sx;
            double y = sy;
            for (int i = 0; i < refine; ++i)
            {
                ++magpat[(int)y*params->xpixels + (int)x];
                x += right_x;
                y += right_y;
            }
            sx += ldown_x;
            sy += ldown_y;
            right_x += update_x;
            right_y += update_y;
        }
    }
    else
        ll_rayshoot_rect(params, magpat, rect, refine, refine);
}

extern void
ll_rayshoot(struct ll_rayshooter_t *rs, int *magpat, struct ll_rect_t *rect,
            int xrays, int yrays, unsigned levels, double *progress)
{
    if (rs->cancel)
        return;
    if (levels)
    {
        double width_per_xrays = (rect->x1 - rect->x0) / xrays;
        double height_per_yrays = (rect->y1 - rect->y0) / yrays;
        bool hit[(xrays+3)*(yrays+3)];
        double mag_x, mag_y;
        for (int j = -1, m = 0; j <= yrays+1; ++j)
            for (int i = -1; i <= xrays+1; ++i, ++m)
                hit[m] = ll_shoot_single_ray(rs->params,
                                             rect->x0 + i*width_per_xrays,
                                             rect->y0 + j*height_per_yrays,
                                             &mag_x, &mag_y);
        bool hit_dilated[(xrays+1)*(yrays+1)];
        for (int j = 0, m = xrays+4, n = 0; j <= yrays; ++j, m += 2)
            for (int i = 0; i <= xrays; ++i, ++m, ++n)
                hit_dilated[n] = (hit[m] ||
                                  hit[m-1] || hit[m-xrays-3] ||
                                  hit[m+1] || hit[m+xrays+3]);
        *progress = 0.0;
        double progress_inc = 1.0 / (xrays*yrays);
        for (int j = 0, n = 0; j < yrays; ++j, ++n)
            for (int i = 0; i < xrays; ++i, ++n, *progress += progress_inc)
                if (hit_dilated[n] || hit_dilated[n+1] ||
                    hit_dilated[n+xrays+1] || hit_dilated[n+xrays+2])
                {
                    double x = rect->x0 + i*width_per_xrays;
                    double y = rect->y0 + j*height_per_yrays;
                    struct ll_rect_t subrect
                        = {x, y, x+width_per_xrays, y+height_per_yrays};
                    double dummy;
                    ll_rayshoot(rs, magpat, &subrect, rs->refine,
                                rs->refine, levels-1, &dummy);
                }
    }
    else
        ll_rayshoot_bilinear(rs->params, magpat, rect, rs->refine_final);
}

extern void
ll_image_from_magpat(char *buf, int *magpat, unsigned size)
{
    int max_count = 0;
    int min_count = MAXINT;
    for(unsigned i = 0; i < size; ++i)
    {
        if (magpat[i] > max_count)
            max_count = magpat[i];
        if (magpat[i] < min_count)
            min_count = magpat[i];
    }
    if (max_count == min_count)
        return;
    double logmax = log(max_count+1);
    double logmin = log(min_count+1);
    double factor = 255/(logmax-logmin);
    for(unsigned i = 0; i < size; ++i)
        buf[i] = 255 - (log(magpat[i]+1)-logmin)*factor;
}

extern void
ll_light_curve(struct ll_magpattern_param_t *params, int *magpat,
               double *curve, unsigned num_points,
               double x0, double y0, double x1, double y1)
{
    double mag_x = (x0 - params->region.x0) * params->pixels_per_width;
    double mag_y = (y0 - params->region.y0) * params->pixels_per_height;
    double dx = (x1 - x0) * params->pixels_per_width / (num_points - 1);
    double dy = (y1 - y0) * params->pixels_per_height / (num_points - 1);
    for (unsigned i = 0; i < num_points; ++i)
    {
        int ix = mag_x;
        int iy = mag_y;
        int index = iy*params->xpixels + ix;
        double frac_x = mag_x - ix;
        double frac_y = mag_y - iy;
        curve[i] = (1.0 - frac_x) * (1.0 - frac_y) * magpat[index]
            + frac_x * (1.0 - frac_y) * magpat[index+1]
            + (1.0 - frac_x) * frac_y * magpat[index+params->xpixels]
            + frac_x * frac_y * magpat[index+params->xpixels+1];
        mag_x += dx;
        mag_y += dy;
    }
}
